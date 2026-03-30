"""
A policy is a way to run an argument

Policies decide how the conversation will go

You can make your own policies by overriding key methods, or you can
use the default policies

see [example of DummyPolicy](https://github.com/JarbasAl/difficult_dialogs/blob/master/examples/dummy_policy.py)

- argument.intro is spoken on start, it is meant to introduce the argument

- a .premise file will be picked randomly and read

- all statements inside a .premise file will be read, but in a random order

- no statements will be repeated

- when all statements inside a .premise file are read, another .premise
file will be picked

- when all .premise files are read, argument.conclusion is printed fully,
it is meant to deliver the conclusion we want to reach

```python
from os.path import join, dirname

from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import KnowItAllPolicy, BasePolicy

arg_folder = join(dirname(__file__), "i_think_therefore_i_am")
arg = Argument(path=arg_folder)

# ignore user input, just go trough all premises
# dialog = BasePolicy(argument=arg)

# defend when user disagrees
dialog = KnowItAllPolicy(arg)


# argument / user loop
dialog.run_async()

while True:
    try:
        if dialog.output:
            print("BOT: " + dialog.output)
            if not dialog.finished:
                utterance = input("USER: ")
                dialog.submit_input(utterance)
            else:
                break
    except KeyboardInterrupt:
        dialog.finished = True
        break

dialog.stop()
```

You also have access to lower level details, policies can be used without the run() loop

```python
from os.path import join, dirname

from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import BasePolicy

arg_folder = join(dirname(__file__), "argument_template")
arg = Argument(path=arg_folder)
dialog = BasePolicy(argument=arg)

# argument manual control
print(dialog.start())
while not dialog.finished:
    assertion = dialog.choose_premise()
    if assertion:
        print(assertion)
        for s in assertion.statements:
            print(s)
        print(assertion.sources)
    else:
        print(dialog.end())
```
"""

import random
from time import sleep
from threading import Thread
from logging import getLogger
from typing import Optional, Union

log = getLogger("DialogRunner")


class BasePolicy:
    """Template Policy that implements minimal functionality to run an argument."""

    def __init__(self, name: str = "base", argument: Optional[object] = None) -> None:
        """

        Args:
            name:
            argument:
        """
        self.name = name
        self.current_statement = None
        self.current_premise = None
        self._cache = []
        self.last_dialog = None
        self.finished = False
        self._in_agreement = True
        self.argument = argument
        self._output = ""
        self._input = ""
        self._async_thread = None
        self._skip_feedback = False
        self._last_prompt = ""

    # lib
    def bind(self, argument):
        """

        Args:
            argument:
        """
        self.argument = argument
        self.argument.load()

    def reset(self):
        """

        """
        self._in_agreement = True
        self.current_premise = None
        self.current_statement = None
        self._cache = []
        self.last_dialog = None
        self.finished = False

    def speak(self, text):
        """
        - normalize text
        - cache response, self._cache_this(text)
        - manage output, self._output += text
        - return normalized text

         """
        text = str(text).strip()
        self._cache_this(text)
        if self._output and not self._output.endswith("\n"):
            self._output += "\n"
        self._output += text
        return text

    def is_cached(self, entry):
        """
        check if entry was used already

        Args:
            entry: text or Statement

        Returns: is_cached (bool)

        """
        entry = str(entry).strip()
        return entry in self.already_spoken

    def _cache_this(self, entry):
        """

        Args:
            entry:
        """
        entry = str(entry).strip()
        self._cache.append(entry)

    def _clean_prompt(self, prompt):
        """

        Args:
            prompt:

        Returns:

        """
        prompt = prompt or "Do you agree with {{statement}} ?"
        if isinstance(prompt, list):
            prompt = random.choice(prompt)
        if self.current_statement is not None:
            current_statement = self.current_statement.text.strip()
        else:
            current_statement = "what i just said"
        prompt = prompt \
            .replace("{{statement}}", current_statement) \
            .replace("{statement}", current_statement) \
            .replace("{{ statement }}", current_statement) \
            .replace("{ statement }", current_statement)
        return prompt + " "

    # dialog data
    @property
    def user_agrees(self):
        """
        Does the user agree with the argument

        Returns: in_agreement (bool)

        """
        return self._in_agreement

    @property
    def already_spoken(self):
        """

        Returns: already spoken responses (list)

        """
        return self._cache

    @property
    def output(self):
        """

        Returns: current bot dialog (str)

        """
        return self._output

    @property
    def intro_statement(self):
        """

        Returns: argument introduction (str)

        """
        if self.argument is not None:
            return str(self.argument.intro_statement)
        return ""

    @property
    def conclusion_statement(self):
        """

        Returns: argument conclusion (str)

        """
        if self.argument is not None:
            return self.argument.conclusion_statement
        return ""

    @property
    def premises(self):
        """

        Returns: all premises of this argument (list)

        """
        if self.argument is not None:
            return self.argument.premises
        return []

    # dialog actions
    def start(self):
        """ prepare context of dialog

        - reset policy, self.reset()
        - set running flag, self.finished = False
        - speak intro statement

        Returns: intro statement (str)

        """
        self.reset()
        self.finished = False
        return self.speak(self.intro_statement)

    def end(self):
        """ handle outcome of dialog

        - unset running flag, self.finished = True
        - return speak conclusion statement

        Returns: conclusion statement (str)

        """
        self.finished = True
        return self.speak(self.conclusion_statement)

    def choose_premise(self, argument=None):
        """
        select which Premise to tackle next

        Returns: next premise (Premise)
        """
        argument = argument or self.argument
        choices = [t for t in argument.premises
                   if not self.is_cached(t)]
        if not len(choices):
            return None
        assertion = random.choice(choices)
        self._cache_this(assertion)  # remember assertion
        return assertion

    def choose_next_statement(self, premise=None):
        """
        select which Statement to tackle next

        Returns: next statement (Statement)
        """
        premise = premise or self.current_premise
        choices = [t for t in premise.statements
                   if not self.is_cached(t)]
        if not len(choices):
            # go to next premise
            next_assertion = self.choose_premise()
            if next_assertion is None:
                self.finished = True
                return None  # no statements left
            self.current_premise = next_assertion
            return self.choose_next_statement()

        statement = random.choice(choices)
        self.current_statement = statement
        return statement

    def agree(self):
        """
        Agree with current premise
        """
        self._in_agreement = True

    def disagree(self):
        """
        Disagree with current premise
        """
        self._in_agreement = False

    def what(self, default_answer="i don't know how to explain"):
        """ explain current statement """
        answer = default_answer
        choices = [t for t in self.current_premise.what
                   if not self.is_cached(t)]
        if len(choices):
            answer = random.choice(choices)
        return self.speak(answer)

    def why(self, default_answer="i don't know why"):
        """ explain cause of current statement """
        answer = default_answer
        choices = [t for t in self.current_premise.why
                   if not self.is_cached(t)]
        if len(choices):
            answer = choices[0]

        return self.speak(answer)

    def how(self, default_answer="i don't know how"):
        """ explain how current statement """
        answer = default_answer
        choices = [t for t in self.current_premise.how
                   if not self.is_cached(t)]
        if len(choices):
            answer = random.choice(choices)

        return self.speak(answer)

    def when(self, default_answer="i don't know when"):
        """ explain when current statement happened """
        answer = default_answer
        choices = [t for t in self.current_premise.when
                   if not self.is_cached(t)]
        if len(choices):
            answer = random.choice(choices)

        return self.speak(answer)

    def where(self, default_answer="i don't know where"):
        """ explain where current statement happened """
        answer = default_answer
        choices = [t for t in self.current_premise.where
                   if not self.is_cached(t)]
        if len(choices):
            answer = random.choice(choices)

        return self.speak(answer)

    def sources(self, default_answer="i don't remember where i learned this"):
        """ sources of current statement """
        answer = default_answer
        if len(self.current_premise.sources):
            answer = " ".join(self.current_premise.sources)
        return answer

    def skip_feedback(self):
        """
        Do not ask for user feedback
        """
        self._skip_feedback = True

    def reprompt(self):
        """

        Speak last used prompt

        Returns: last prompt (str)

        """
        return self.speak(self._last_prompt)

    # sync
    def _run_once(self):
        """

        Returns:

        """
        # check if argument is fully exposed
        if self.finished:
            return None

        # check if we have an assertion
        if self.current_premise is None:
            current_assertion = self.choose_premise()
            self.current_premise = current_assertion

        # pick action
        if not self.user_agrees:
            return self.on_negative_feedback()
        else:
            return self.on_positive_feedback()

    def run(self):
        """ run the interaction, ask if user agrees or not after every
        statement

        NOTE: ignores on user input callback, mostly meant for quick testing
        """
        # introduce argument
        print(self.start())
        while not self.finished:
            try:
                # choose output
                output = self._run_once()
                if output is None:
                    # wait for output
                    continue
                print(output)
                if self.finished:
                    break
                # get user feedback
                if self._skip_feedback:
                    self._skip_feedback = False
                    continue
                if self.get_feedback():
                    self.agree()
                else:
                    self.disagree()

            except Exception as e:
                log.exception(e)
        # finish off argument
        print(self.end())

    def get_feedback(self, prompt=None):
        """
        used in run(), if running async wait_for_feedback is used instead

        ask user if he agrees with current statement or not

        prompt is a string or list of strings, if it's a list a random entry will be picked

        return True or False """
        prompt = self._clean_prompt(prompt)
        self._last_prompt = prompt
        return "y" in input(prompt).lower()

    # async
    def wait_for_input(self):
        """
        wait until self.submit_input is called
        """
        self._input = ""
        while not self._input:
            sleep(0.5)

    def wait_for_feedback(self, prompt=None):
        """
        ask user if he agrees with current statement or not

        prompt is a string or list of strings, if it's a list a random entry will be picked

        return True or False """
        prompt = self._clean_prompt(prompt)
        self._output += "\n" + prompt
        self._last_prompt = prompt
        self.wait_for_input()
        return "y" in self._input.lower()

    def submit_input(self, text):
        """

        Args:
            text: utterance (str)
        """
        self._output = ""
        if self.on_user_input(text):
            self._input = text

    def run_async(self):
        """
        Start listening for user input
        """
        self._async_thread = Thread(target=self._async_loop)
        self._async_thread.setDaemon(True)
        self._async_thread.start()

    def stop(self):
        """
        Stop listening for user input
        """
        self.finished = True
        try:
            self._async_thread.join()
            self._async_thread.cancel()
        except:
            pass
        self._async_thread = None

    def _async_loop(self):
        """ run the interaction async """
        # introduce argument
        self.start()
        while not self.finished:
            try:
                # choose output
                if not self._run_once():
                    continue

                if self._skip_feedback:
                    self._skip_feedback = False
                    continue
                # get user feedback
                if self.wait_for_feedback():
                    self.agree()
                else:
                    self.disagree()
            except Exception as e:
                log.exception(e)
        # finish off argument
        self.end()

    # events
    def on_user_input(self, text):
        """ handle user input

        intent parsing should be done here

        typical actions are

        - calling self.agree() or self.disagree() to direct the policy (return True)
        - calling self.what(), self.why(), self.how(), self.when(),
        self.where() and setting the output (return False)

        NOTE: only when running async

        return True or False, this determines if dialog should proceed or
        wait for different user input

        """
        return True

    def on_positive_feedback(self):
        """ react to positive feedback

        by default goes to next statement

        """
        statement = self.choose_next_statement()
        if not statement:
            return None
        return self.speak(statement)

    def on_negative_feedback(self):
        """ react to negative feedback

        by default goes to next statement
        """
        statement = self.choose_next_statement()
        if not statement:
            return None
        return self.speak(statement)


class KnowItAllPolicy(BasePolicy):
    """
    Policy that implements minimal corrective action on negative feedback
    """

    def __init__(self, argument):
        """

        Args:
            argument:
        """
        BasePolicy.__init__(self, name="KnowItAll", argument=argument)

    def on_user_input(self, text):
        """

        answer to the [Five Ws](https://en.wikipedia.org/wiki/Five_Ws)

        - Who was involved?
        - What happened?
        - Where did it take place?
        - When did it take place?
        - Why did that happen?

        """
        if "what" in text:
            self.what()
            self.reprompt()
        elif "why" in text:
            self.why()
            self.reprompt()
        elif "how" in text:
            self.how()
            self.reprompt()
        elif "where" in text:
            self.where()
            self.reprompt()
        elif "when" in text:
            self.when()
            self.reprompt()
        else:
            return True
        return False

    def on_negative_feedback(self):
        """
        react to negative feedback

        speak a support statement

        if no more support statements call on_complete_failure
        """
        assertion = self.current_premise
        # comeback with support statement
        choices = [t for t in assertion.support_statements
                   if not self.is_cached(t)]

        if not len(choices):
            statement = self.on_complete_failure()
        else:
            statement = random.choice(choices)
        return self.speak(statement)

    def on_complete_failure(self):
        """
        handle failure to get a response, called by on_negative_feedback if
        no support statements available

        speak the sources of the premise, accept defeat, or force agreement

        Returns:
            sentence to speak (str)
        """
        if not len(self.current_premise.sources):
            # agree on failure
            self.agree()
            self.skip_feedback()
            choices = ["I guess you are right",
                       "You may be right, i'll give it further thought",
                       "I'm not so sure anymore, i will think about it",
                       "I may be wrong"]

        else:
            # let's just show the sources
            source_str = "here is the source of my information\n"
            source_str += "\n".join(self.current_premise.sources)

            choices = [source_str]
        choices = [c for c in choices if not self.is_cached(c)]
        if not len(choices):
            self.agree()
            self.skip_feedback()
            choices = ["We will have to agree to disagree for now"]
        return random.choice(choices)
