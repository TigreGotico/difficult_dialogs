"""
A premise is a set of Statements, a premise is True if all it's statements are True

A premise also has sources to back it up, and support dialog that can be interjected at will

```python
from difficult_dialogs.premises import Premise

p = Premise("pizza tastes good")
p.add_statement("pizza is food")
p.add_statement("the taste of pizza is pleasant")
p.add_support_statement("i like pizza")
p.add_source("http://pizza_reviews.com")

for s in p.statements:
    assert s.is_true
assert bool(p) == True

p.statements[0].disagree()

assert bool(p) == False

assert p.as_json == {'is_true': False,
                     'sources': ['http://pizza_reviews.com'],
                     'statements': ['pizza is food',
                                    'the taste of pizza is pleasant'],
                     'support': ['i like pizza'],
                     'description': 'pizza tastes good'}
```
"""

from typing import Any, Optional, Union

from difficult_dialogs.statements import Statement
from difficult_dialogs.exceptions import UnrecognizedStatementFormat, \
    UnrecognizedDescriptionFormat


class Premise:

    def __init__(self, description: Union[str, Statement],
                 statements: Optional[list[Union[str, Statement]]] = None,
                 sources: Optional[list[str]] = None,
                 support: Optional[list[Union[str, Statement]]] = None,
                 what: Optional[list[Union[str, Statement]]] = None,
                 when: Optional[list[Union[str, Statement]]] = None,
                 where: Optional[list[Union[str, Statement]]] = None,
                 how: Optional[list[Union[str, Statement]]] = None,
                 why: Optional[list[Union[str, Statement]]] = None) -> None:
        """

        A premise is a core assumption of an argument

        All statements in a premise need to be said, in no particular order, to understand the premise

        A premise is True if all it's statements are True

        A Premise contains:
        - support statements - sentences that can be said at any time in
        support of the premise
        - sources - urls or strings identifying the source of the
        information this premise is based on

        Premises provide answer to the [Five Ws](https://en.wikipedia.org/wiki/Five_Ws)
        - Who was involved?
        - What happened?
        - Where did it take place?
        - When did it take place?
        - Why did that happen?

        Args:
            description:
            statements:
            sources:
            support:
            what:
            when:
            where:
            how:
            why:
        """
        statements = statements or []
        self.statements = []
        for s in statements:
            s = self.validate_statement(s)
            self.statements.append(s)

        support = support or []
        self.support_statements = []
        for s in support:
            s = self.validate_statement(s)
            self.support_statements.append(s)

        self.sources = sources or []
        self.what = []
        what = what or []
        for s in what:
            s = self.validate_statement(s)
            self.what.append(s)
        self.when = []
        when = when or []
        for s in when:
            s = self.validate_statement(s)
            self.when.append(s)
        self.where = []
        where = where or []
        for s in where:
            s = self.validate_statement(s)
            self.where.append(s)
        self.how = []
        how = how or []
        for s in how:
            s = self.validate_statement(s)
            self.how.append(s)
        self.why = []
        why = why or []
        for s in why:
            s = self.validate_statement(s)
            self.why.append(s)
        self.description = self.validate_statement(description)

    def agree(self) -> None:
        """ flag all statements as True """
        for idx, s in enumerate(self.support_statements):
            self.support_statements[idx].agree()
        for idx, s in enumerate(self.statements):
            self.statements[idx].agree()

    @staticmethod
    def validate_statement(statement: Union[str, Statement]) -> Statement:
        """

        Args:
            statement:

        Returns:

        """
        if isinstance(statement, str):
            statement = Statement(statement)
        if not isinstance(statement, Statement):
            raise UnrecognizedStatementFormat
        return statement

    def from_json(self, json_dict: dict[str, Any]) -> None:
        """

        Args:
            json_dict:
        """
        self.description = json_dict.get("description", self.description)
        for s in json_dict.get("sources"):
            self.add_source(s)
        for s in json_dict.get("statements"):
            self.add_statement(s)
        for s in json_dict.get("support"):
            self.add_support_statement(s)

    @property
    def as_json(self) -> dict[str, Any]:
        """

        Returns:

        """
        return {"description": self.description.text,
                "sources": self.sources,
                "statements": [s.text for s in self.statements],
                "support": [s.text for s in self.support_statements],
                "what": [s.text for s in self.what],
                "why": [s.text for s in self.why],
                "when": [s.text for s in self.when],
                "where": [s.text for s in self.where],
                "how": [s.text for s in self.how],
                "is_true": self.is_true}

    def update(self, premise):
        """
        if premise is an Premise object or dictionary, statements,
        support and sources will be merged

        if premise is a string, a support statement will be merged

        if premise is a list, each item will be added recursively
        """
        if isinstance(premise, Premise):
            self.update(premise.as_json)
        elif isinstance(premise, str):
            self.add_support_statement(premise)
        elif isinstance(premise, dict):
            statements = premise.get("statements", [])
            for s in statements:
                self.add_statement(s)
            statements = premise.get("support", [])
            for s in statements:
                self.add_support_statement(s)
            sources = premise.get("sources", [])
            for s in sources:
                self.add_source(s)
            statements = premise.get("what", [])
            for s in statements:
                self.add_what_statement(s)
            statements = premise.get("when", [])
            for s in statements:
                self.add_when_statement(s)
            statements = premise.get("why", [])
            for s in statements:
                self.add_why_statement(s)
            statements = premise.get("where", [])
            for s in statements:
                self.add_where_statement(s)
            statements = premise.get("how", [])
            for s in statements:
                self.add_how_statement(s)
        elif isinstance(premise, list):
            for s in premise:
                self.update(s)

    def set_description(self, text):
        """ set premise description from string"""
        if not isinstance(text, str) and not isinstance(text, Statement):
            raise UnrecognizedDescriptionFormat("description of a Premise "
                                                "must be a string or "
                                                "Statement")
        self.description = text

    def add_source(self, text: str) -> None:
        """

        Args:
            text:
        """
        if text not in self.sources:
            self.sources.append(text)

    def add_statement(self, text: Union[str, Statement]) -> None:
        """

        Args:
            text:
        """
        print(text)
        text = self.validate_statement(text)
        if text not in self.statements:
            self.statements.append(text)

    def add_support_statement(self, text: Union[str, Statement]) -> None:
        """

        Args:
            text:
        """
        text = self.validate_statement(text)
        if text not in self.support_statements:
            self.support_statements.append(text)

    def add_what_statement(self, text):
        """

        Args:
            text:
        """
        text = self.validate_statement(text)
        if text not in self.what:
            self.what.append(text)

    def add_when_statement(self, text):
        """

        Args:
            text:
        """
        text = self.validate_statement(text)
        if text not in self.when:
            self.when.append(text)

    def add_where_statement(self, text):
        """

        Args:
            text:
        """
        text = self.validate_statement(text)
        if text not in self.where:
            self.where.append(text)

    def add_how_statement(self, text):
        """

        Args:
            text:
        """
        text = self.validate_statement(text)
        if text not in self.how:
            self.how.append(text)

    def add_why_statement(self, text):
        """

        Args:
            text:
        """
        text = self.validate_statement(text)
        if text not in self.why:
            self.why.append(text)

    @property
    def is_true(self) -> bool:
        """ premises are true if all their statements are true """
        for s in self.statements:
            if not s.is_true:
                return False
        return True

    @property
    def stats(self):
        """ return dictionary with stats about premise """
        return {"num_statements": len(self.statements),
                "num_support": len(self.support_statements),
                "num_sources": len(self.sources),
                "is_true": self.is_true}

    def __str__(self):
        """

        Returns:

        """
        return self.description.text

    def __bool__(self):
        """

        Returns:

        """
        return self.is_true
