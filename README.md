# Room2room-Tour
This is the GitHub repository of the Room2room Tour project, the essence of which is to create a platform to reduce the cost of traveling in Russia through a housing exchange mechanism, as well as providing communication between people from different cities of Russia for "remote" tourism.

## Database configuration

Set `DATABASE_URL` in your environment. If you provide an asyncpg URL, it will be converted automatically to a sync driver for Flask-SQLAlchemy.

Example:

```
DATABASE_URL=postgresql+asyncpg://postgres:SpeedcubingVK7@localhost:5434/Room2roomTourDatabase
```