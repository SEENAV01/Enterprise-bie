"""Precision-aware civil-date intervals in an explicit proleptic Gregorian model.

BCE/CE notation has no civil year zero. Astronomical year 0 represents 1 BCE.
This module does NOT guess/convert historical Julian or regional calendars.
"""
from __future__ import annotations
from ..models import BenchmarkError
from .common import integer
from .structured import choice, record


def astronomical_year(year: object, era: object) -> int:
    y=integer(year,1,9999)
    return y if choice(era,{'CE','BCE'})=='CE' else 1-y


def month_length(year: int, month: int) -> int:
    if month==2:
        return 29 if year%4==0 and (year%100!=0 or year%400==0) else 28
    return 30 if month in (4,6,9,11) else 31


def day_number(year: int, month: int, day: int) -> int:
    # Integer Gregorian Julian-day-number conversion. Only differences matter.
    a=(14-month)//12;y=year+4800-a;m=month+12*a-3
    return day+(153*m+2)//5+365*y+y//4-y//100+y//400-32045


def date_interval(value: object) -> tuple[int,int]:
    if type(value) is not dict:
        raise BenchmarkError('INVALID_FIELDS')
    precision=choice(value.get('precision'),{'year','month','day'})
    fields={'year','era','precision','calendar'}
    if precision in ('month','day'):fields.add('month')
    if precision=='day':fields.add('day')
    record(value, fields)
    choice(value['calendar'],{'proleptic_gregorian'})
    year=astronomical_year(value['year'],value['era'])
    if precision=='year':
        return day_number(year,1,1),day_number(year,12,31)
    month=integer(value['month'],1,12)
    if precision=='month':
        return day_number(year,month,1),day_number(year,month,month_length(year,month))
    day=integer(value['day'],1,month_length(year,month))
    n=day_number(year,month,day)
    return n,n


def relation(a: tuple[int,int], b: tuple[int,int]) -> str:
    if a[1]<b[0]:return 'BEFORE'
    if a[0]>b[1]:return 'AFTER'
    if a[0]==a[1]==b[0]==b[1]:return 'SAME_DAY'
    return 'OVERLAPPING_OR_UNCERTAIN'
