#kiírja a motor aktuális állapotát (MODE és REASON_FOR_STOP)

import asyncio
import moteus

async def main():
    m = moteus.Controller(id=1)

    state = await m.query()

    mode = state.values[moteus.Register.MODE]
    reason = state.values[moteus.Register.REASON_FOR_STOP]

    print(f"Aktuális mód (MODE): {mode}")
    print(f"Leállás oka (REASON_FOR_STOP): {reason}")

if __name__ == '__main__':
    asyncio.run(main())