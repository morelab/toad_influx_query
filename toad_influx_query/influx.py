import aioinflux
import re as regex
import strict_rfc3339

from toad_influx_query.config import INFLUX_HOST, INFLUX_PORT  # INFLUX_DB
from toad_influx_query import protocol as proto


class QueryParseException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Query:
    """Query represents an InfluxDB query sent by the toad_api module."""

    def __init__(self, topic: str, payload: dict):
        self.response_topic = payload[proto.RESPONSE_ID_FIELD]

        t = topic.split("/")
        self.measure = t[-1]
        self.db = t[-2]

        data = payload[proto.DATA_FIELD]
        self.operation = data.get(proto.OP_FIELD)
        self.type = data.get(proto.TYPE_FIELD)
        self.id = data.get(proto.ID_FIELD)
        self.row = data.get(proto.ROW_FIELD)
        self.col = data.get(proto.COLUMN_FIELD)
        self._from = data.get(proto.DATE_FROM_FIELD)
        self._to = data.get(proto.DATE_TO_FIELD)

        err = self.parse()
        if err != "":
            raise QueryParseException(err)

    def parse(self) -> str:
        """
        Parse a query.

        Checks the validity of each field. It is necessary to run
        this function before running the query to avoid injection.
        :return: Empty string if OK, parsing error string if not OK.
        """

        reasons = []

        # Measurement
        if self.measure not in proto.MEASURES:
            reasons.append(
                "Invalid measurement '{}', must be one of '{}'".format(
                    self.measure, proto.MEASURES
                )
            )

        # Operation
        _op = self.operation
        if _op:
            self.operation = _op = _op.upper()
            if _op not in proto.OPERATIONS:
                reasons.append(
                    "Invalid operation '{}', must be one of '{}'".format(
                        _op, proto.OPERATIONS
                    )
                )

        # Type
        _type = self.type
        if _type and _type not in proto.TYPES:
            reasons.append(
                "Invalid type '{}', must be one of '{}'".format(_type, proto.TYPES)
            )

        # ID
        _id = self.id
        if _id is not None and not regex.fullmatch(proto.ID_REGEX, _id):
            reasons.append(f"Invalid ID {_id}")

        # Row
        _row = self.row
        if _row is not None:
            if _id:
                reasons.append(
                    f"Specified both a row and an identifier. Please choose one"
                    + "or run multiple queries"
                )
            try:
                self.row = int(_row)
            except ValueError:
                reasons.append(f"Invalid row '{_row}'")

        # Column
        _col = self.col
        if _col is not None:
            if _id:
                reasons.append(
                    f"Specified both a column and an identifier. Please choose one"
                    + "or run multiple queries"
                )
            try:
                self.col = int(_col)
            except ValueError:
                reasons.append(f"Invalid column '{_col}'")

        # FROM date
        _from = self._from
        if _from is not None:
            try:
                if not regex.fullmatch(proto.DATETIME_REGEX, _from):
                    # timestamp_to_rfc3339_utcoffset
                    self._from = strict_rfc3339.timestamp_to_rfc3339_localoffset(
                        float(_from)
                    )
            except (TypeError, ValueError):
                reasons.append(f"Invalid FROM date {_from}")

        # TO date
        _to = self._to
        if _to is not None:
            try:
                if not regex.fullmatch(proto.DATETIME_REGEX, _to):
                    self._to = strict_rfc3339.timestamp_to_rfc3339_localoffset(float(_to))
            except (TypeError, ValueError):
                reasons.append(f"Invalid TO date {_to}")

        return ". ".join(reasons)

    def __str__(self) -> str:
        # select value from
        if self.operation:
            query = f'SELECT {self.operation}("value") FROM "{self.measure}" '
        else:
            query = f'SELECT "value" FROM "{self.measure}" '
        filter_started = False
        if self.id is not None:
            query += f"WHERE \"id\" = '{self.id}' "
            filter_started = True
        if self.row is not None:
            query += f"WHERE \"row\" = '{self.row}' "
            filter_started = True
        if self.col is not None:
            query += f"{'AND' if filter_started else 'WHERE'} \"column\" = '{self.col}' "
            filter_started = True
        if self.type is not None:
            query += f"{'AND' if filter_started else 'WHERE'} \"type\" = '{self.type}'"
            filter_started = True
        if self._from is not None:
            query += f"{'AND' if filter_started else 'WHERE'} time >= '{self._from}'"
            filter_started = True
        if self._to is not None:
            query += f"{'AND' if filter_started else 'WHERE'} time <= '{self._to}'"

        return query

    async def run(self) -> aioinflux.client.ResultType:
        """
        Send the query to Influx and return the results
        :return:
        """
        async with aioinflux.InfluxDBClient(
            host=INFLUX_HOST, port=INFLUX_PORT, db=self.db  # db=INFLUX_DB
        ) as client:
            return await client.query(self.__str__())
