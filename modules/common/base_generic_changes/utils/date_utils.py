# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

from pytz import timezone, utc

from odoo import fields
from odoo.exceptions import UserError


def _local_tz(env):
    """
        If the user has a timezone configured in their browser then we use that for localisation
        Otherwise we raise a warning
        @return user's timezone
    """
    # User"s local timezone, as configured in the browser
    if "tz" not in env.context or not env.context["tz"]:
        if env.user.partner_id.tz:
            context = dict(env.context)
            context["tz"] = env.user.partner_id.tz
            env.context = context
        else:
            raise Warning(
                "The timezone in your client has not been configured. "
                "Failure to correctly configure the timezone will cause data storage issues.")
    return timezone(env.context["tz"])


def _check_datetime(datetime_to_chk):
    """
        We can only convert string to fields.Date or fields.Datetime
        So, if the datetime_to_chk comes in as a type we can convert to string, we do that
        @return string
    """
    # strings are what we want
    if isinstance(datetime_to_chk, str):
        return datetime_to_chk

    # Unicode gets converted to a string
    if isinstance(datetime_to_chk, bytes):
        return str(datetime_to_chk)

    # Datetime
    if isinstance(datetime_to_chk, (datetime, fields.Datetime)):
        return fields.Datetime.to_string(datetime_to_chk)

    # Date
    if isinstance(datetime_to_chk, (date, fields.Date)):
        return fields.Date.to_string(datetime_to_chk)

    # We've gotten something bad
    raise Warning("Cannot convert %s to Date or Datetime string", type(datetime_to_chk))


def convert_datetime_to_utc(reference_datetime, env):
    """
        Take a local datetime and convert it to UTC in readiness for storing in the Database
        We assume that the datetime supplied is naive, that is, it's not tz aware
        @return datetime string converted to UTC
    """

    local_tz = _local_tz(env)

    reference_datetime = _check_datetime(reference_datetime)
    return fields.Datetime(
        local_tz.localize(fields.Datetime.from_string(reference_datetime)).astimezone(utc))


def convert_datetime_to_local(reference_datetime, env):
    """
        Take a UTC datetime and convert it to localtime in readiness for sending to the user.

        This uses the timezone from the context in the passed environment.
        We assume that the datetime supplied is naive, that is, it"s not tz aware

        Args:
            reference_datetime: can be a datetime or an Odoo datetime string
            env: environment to use for localising.

        @return An Odoo datetime string
    """

    local_tz = _local_tz(env)

    reference_datetime = _check_datetime(reference_datetime)
    return fields.Datetime.to_string(
        utc.localize(fields.Datetime.from_string(reference_datetime)).astimezone(local_tz))


class RosterDateTimeBase(object):
    # assume we get str from utc

    def __init__(self, tz):
        self.local_tz = self.get_local_tz(tz)

    @staticmethod
    def get_local_tz(tz):
        """
        If the user has a timezone configured in their browser then we use that for localisation
        Otherwise we raise a warning.
        @return:
        """
        if not tz:
            raise UserError("The timezone is not configured, please check your company settings")
        return timezone(tz)

    @staticmethod
    def time_to_float(time_obj):
        return timedelta(hours=time_obj.hour, minutes=time_obj.minute).total_seconds() / 3600

    @staticmethod
    def time_to_string(time_obj):
        return "{:02d}:{:02d}:00".format(time_obj.hour, time_obj.minute)


class RosterDatetime(RosterDateTimeBase):

    def __init__(self, datetime_str, tz):
        super(RosterDatetime, self).__init__(tz)
        self.datetime_str = datetime_str

    def from_string(self, date_str):
        return fields.Datetime.from_string(date_str)

    def to_string(self, date_obj):
        if not isinstance(date_obj, datetime):
            raise UserError("Conversion from Datetime obj to string: missing object.")
        return fields.Datetime.to_string(date_obj)

    def get_utc_datetime(self):
        """
        Careful! Don't supply string which is already made from UTC time
        :return:
        """
        datetime_obj = self.from_string(self.datetime_str)
        return self.local_tz.localize(datetime_obj).astimezone(utc)

    def get_datetime_in_timezone(self):
        datetime_obj = self.from_string(self.datetime_str)
        return utc.localize(datetime_obj).astimezone(self.local_tz)

    def get_datetime_midnight(self):
        """
        :return: Midnight datetime of string you've provided
        """
        dt_obj = self.from_string(self.datetime_str)
        midnight_datetime = datetime(day=dt_obj.day, month=dt_obj.month, year=dt_obj.year, hour=0,
                                     minute=0, second=0)
        return midnight_datetime

    def get_utc_midnight(self):
        utc_time = self.get_utc_datetime()
        midnight_datetime = datetime(day=utc_time.day, month=utc_time.month, year=utc_time.year, hour=0,
                                     minute=0, second=0)
        return midnight_datetime

    def get_date_in_timezone(self):
        local_datetime = self.get_datetime_in_timezone()
        return local_datetime.date()

    def get_time_in_timezone(self):
        local_datetime = self.get_datetime_in_timezone()
        return local_datetime.time()

    def get_date(self):
        datetime_obj = self.from_string(self.datetime_str)
        return datetime_obj.date()

    def get_time(self):
        datetime_obj = self.from_string(self.datetime_str)
        return datetime_obj.time()

    ###########################################################################
    # Properties
    ###########################################################################

    # datetime related properties

    @property
    def datetime_tz(self):
        return self.get_datetime_in_timezone()

    @property
    def datetime_tz_str(self):
        return self.to_string(self.datetime_tz)

    @property
    def datetime_utc(self):
        return self.get_utc_datetime()

    @property
    def datetime_utc_str(self):
        utc_time = self.get_utc_datetime()
        return self.to_string(utc_time)

    @property
    def datetime_utc_midnight(self):
        return self.get_datetime_midnight()

    @property
    def datetime_utc_midnight_str(self):
        return self.to_string(self.datetime_utc_midnight)

    # date related properties

    @property
    def date_tz(self):
        return self.get_date_in_timezone()

    @property
    def date_tz_str(self):
        return fields.Date.to_string(self.date_tz)

    @property
    def date_utc(self):
        return self.get_date()

    @property
    def date_utc_str(self):
        return fields.Date.to_string(self.get_date())

    # time related properties

    @property
    def time_tz(self):
        return self.get_time_in_timezone()

    @property
    def time_tz_str(self):
        return self.time_to_string(self.time_tz)

    @property
    def time_tz_float(self):
        return self.time_to_float(self.time_tz)

    @property
    def time_utc(self):
        return self.get_time()

    @property
    def time_utc_str(self):
        return self.time_to_string(self.time_utc)

    @property
    def time_utc_float(self):
        return self.time_to_float(self.time_utc)


class RosterFloatTime(RosterDateTimeBase):

    def __init__(self, time_value, tz):
        super(RosterFloatTime, self).__init__(tz)
        self.time_value = time_value

    def validate_time_field(self):
        if not isinstance(self.time_value, float):
            raise UserError("Please use numbers and format 00:00 to set time field")
        if not 0 <= self.time_value <= 23.984:
            raise UserError("Please use time from 00:00 to 23:59")

    def get_time_str(self):
        return '{0:02.0f}:{1:02.0f}:00'.format(*divmod(self.time_value * 60, 60))


class RosterDate(object):

    def __init__(self, data):
        self.date_str = data

    def from_string(self, date_str):
        if not isinstance(date_str, str):
            raise UserError("Convertation from string to Date object: missing string.")
        return fields.Date.from_string(date_str)

    def to_string(self, date_obj):
        if not isinstance(date_obj, date):
            raise UserError("Convertation from Date obj to string: missing object.")
        return fields.Date.to_string(date_obj)

    @property
    def weekday(self):
        date_obj = self.from_string(self.date_str)
        weekday = date_obj.weekday()
        return weekday
