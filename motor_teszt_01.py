# Pozíció lekérdezése a motorból

import asyncio
import moteus

async def main():
    q = moteus.Controller(id=1)
    
    state = await q.query()
    print(f"Motor pozíció: {state.values[moteus.Register.POSITION]} fordulat")

if __name__ == '__main__':
    asyncio.run(main())