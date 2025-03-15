import aiohttp
import asyncio
import icalendar  # https://icalendar.readthedocs.io/en/latest/

from typing import List
from icalendar import Event as _cal_event


class Event:
    def __init__(self, event: _cal_event) -> None:
        self.summary = event.get("SUMMARY")
        self.start_time = event.get("DTSTART").dt
        self.end_time = event.get("DTEND").dt
        self.duration = event.duration


class Calendar:
    def __init__(self, URL: str) -> None:
        """Initialises the Calendar class with the URL"""
        self._URL = URL
        self._calendar = None
        self.events: List[Event] = []

    async def fetch_calendar(self) -> None:
        """Executes a GET request to get the calendar"""
        async with aiohttp.ClientSession() as session:
            resp = await session.get(self._URL)
        
        if resp.status == 200:
            self._calendar = icalendar.Calendar.from_ical(await resp.text())
            self.events.clear()  # Clear the events to put the new ones in
            for event in self._calendar.events:
                self.events.append(Event(event))
        else:
            raise ValueError(f"Could not get calendar, HTTP Error {resp.status}")



async def main():
    calendar_url = "https://my-timetable.monash.edu/odd/rest/calendar/ical/c392fe27-66ce-4992-ba42-09f18e2ea455"

    cal = Calendar(calendar_url)
    await cal.fetch_calendar()
    for event in cal.events:
        print(event.summary)


if __name__ == '__main__':
    asyncio.run(main())
