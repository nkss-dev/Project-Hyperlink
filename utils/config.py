import asyncio
import json
import os
import uuid


class Config:
    """The "database" object. Internally based on ``json``."""

    def __init__(self, name, **options):
        self.name = name

        self.loop = options.pop('loop', asyncio.get_event_loop())
        self.lock = asyncio.Lock()

        if string := options.pop('string', False):
            self._db = json.loads(string)
        else:
            self.load_from_file()

    def load_from_file(self):
        try:
            with open(f'db/{self.name}', 'r') as f:
                self._db = json.load(f)
        except FileNotFoundError:
            self._db = {}

    def _dump(self):
        temp = f'db/{uuid.uuid4()}-{self.name}.tmp'
        with open(temp, 'w') as tmp:
            json.dump(self._db.copy(), tmp)

        os.replace(temp, f'db/{self.name}')

    async def save(self):
        async with self.lock:
            await self.loop.run_in_executor(None, self._dump)

    def get(self, key, *args):
        """Retrieves a config entry."""
        if isinstance(key, (tuple, list)):
            if len(key) > 1:
                return self.get(key[:-1], *args).get(str(key[-1]))
            else:
                return self._db.get(str(key[0]), *args)
        else:
            return self._db.get(str(key), *args)

    async def put(self, keys, value):
        """Edits a config entry."""
        if len(keys) == 3:
            self._db[str(keys[0])][str(keys[1])][str(keys[2])] = value
        elif len(keys) == 2:
            self._db[str(keys[0])][str(keys[1])] = value
        elif len(keys) == 1:
            self._db[str(keys[0])] = value
        await self.save()

    async def append(self, keys, value):
        """Appends to a config entry."""
        if len(keys) == 3:
            self._db[str(keys[0])][str(keys[1])][str(keys[2])].append(value)
        elif len(keys) == 2:
            self._db[str(keys[0])][str(keys[1])].append(value)
        elif len(keys) == 1:
            self._db[str(keys[0])].append(value)
        await self.save()

    async def pop(self, *keys):
        """Removes a config entry."""
        if len(keys) == 3:
            del self._db[str(keys[0])][str(keys[1])][str(keys[2])]
        elif len(keys) == 2:
            del self._db[str(keys[0])][str(keys[1])]
        elif len(keys) == 1:
            del self._db[str(keys[0])]
        await self.save()

    async def remove(self, *keys):
        """Removes a config entry."""
        if len(keys) == 3:
            self._db[str(keys[0])][str(keys[1])].remove(keys[2])
        elif len(keys) == 2:
            self._db[str(keys[0])].remove(keys[1])
        elif len(keys) == 1:
            self._db.remove(keys[0])
        await self.save()

    def __contains__(self, *items):
        db = self._db
        for var in items:
            if str(var) not in db:
                return False
            if items[-1] == var:
                return True
            if isinstance(db[str(var)], dict):
                db = db[str(var)]
            elif isinstance(db[str(var)], (list, tuple)):
                return items[-1] in db[str(var)]
            else:
                return items[-1] == db[str(var)]
        return True

    def __getitem__(self, item):
        return self._db[str(item)]

    def __len__(self):
        return len(self._db)

    def all(self):
        return self._db
