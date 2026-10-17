# Teszt 1: Trapéz pozícióprofil

import asyncio
import time
import csv
import moteus
import matplotlib
matplotlib.use('Agg') # Ablak nélküli (SSH-barát) képgenerálás
import matplotlib.pyplot as plt

async def main():
    # Regiszterek beállítása: bekapcsoljuk az áram és hőmérséklet lekérdezését is!
    qr = moteus.QueryResolution()
    qr.q_current = moteus.F32
    qr.temperature = moteus.F32
    qr._extra = {
        moteus.Register.CONTROL_POSITION: moteus.F32,
        moteus.Register.CONTROL_VELOCITY: moteus.F32,
        moteus.Register.VOLTAGE: moteus.F32,
        moteus.Register.FAULT: moteus.INT8,
    }

    c = moteus.Controller(id=1, query_resolution=qr)

    # 1. Hibák törlése és aktuális pozíció lekérése
    state = await c.set_stop(query=True)
    start_pos = state.values[moteus.Register.POSITION]
    print(f"Induló pozíció: {start_pos:.3f} rev | Feszültség: {state.values[moteus.Register.VOLTAGE]:.1f} V")
    print("Teszt indul (4 másodperc, 100 Hz)...")

    log_data = []
    t0 = time.monotonic()

    try:
        while True:
            t = time.monotonic() - t0
            if t > 4.0:
                break

            # Időzített pálya: 0.5mp-től +1 fordulat, 2.2mp-től vissza az eredetire
            if t < 0.5:
                target_pos = start_pos
            elif t < 2.2:
                target_pos = start_pos + 1.0
            else:
                target_pos = start_pos

            # Parancsküldés 100 Hz-en sebesség- és gyorsuláskorláttal (Trapéz profil)
            state = await c.set_position(
                position=target_pos,
                velocity=0.0,
                velocity_limit=2.0,     # Max 2 fordulat/mp
                accel_limit=6.0,        # Max 6 fordulat/mp^2 gyorsulás
                maximum_torque=0.5,     # Max 0.5 Nm nyomaték
                query=True
            )

            v = state.values
            log_data.append({
                'time': t,
                'cmd_pos': v.get(moteus.Register.CONTROL_POSITION, target_pos),
                'pos': v.get(moteus.Register.POSITION, 0.0),
                'cmd_vel': v.get(moteus.Register.CONTROL_VELOCITY, 0.0),
                'vel': v.get(moteus.Register.VELOCITY, 0.0),
                'torque': v.get(moteus.Register.TORQUE, 0.0),
                'q_curr': v.get(moteus.Register.Q_CURRENT, 0.0),
                'temp': v.get(moteus.Register.TEMPERATURE, 0.0),
                'mode': v.get(moteus.Register.MODE, 0),
                'fault': v.get(moteus.Register.FAULT, 0)
            })

            await asyncio.sleep(0.01) # 10 ms -> ~100 Hz

    finally:
        await c.set_stop()
        print("Motor biztonságosan leállítva.")

    # 2. Adatok mentése CSV-be
    csv_file = "teszt_1_adatok.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=log_data[0].keys())
        writer.writeheader()
        writer.writerows(log_data)
    print(f"Adatok elmentve: {csv_file} ({len(log_data)} mérési pont)")

    # 3. Grafikon generálása (PNG)
    t_arr = [r['time'] for r in log_data]
    fig, axs = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    fig.suptitle('Moteus C1 + mj5208 - 1. Teszt: Trapéz Pozícióprofil', fontsize=14)

    axs[0].plot(t_arr, [r['cmd_pos'] for r in log_data], 'r--', label='Tervezett pozíció (Control)')
    axs[0].plot(t_arr, [r['pos'] for r in log_data], 'b-', label='Valós pozíció')
    axs[0].set_ylabel('Pozíció [rev]')
    axs[0].legend(loc='upper right')
    axs[0].grid(True)

    axs[1].plot(t_arr, [r['cmd_vel'] for r in log_data], 'r--', label='Tervezett sebesség')
    axs[1].plot(t_arr, [r['vel'] for r in log_data], 'g-', label='Valós sebesség')
    axs[1].set_ylabel('Sebesség [rev/s]')
    axs[1].legend(loc='upper right')
    axs[1].grid(True)

    axs[2].plot(t_arr, [r['torque'] for r in log_data], 'm-', label='Nyomaték [Nm]')
    axs[2].set_ylabel('Nyomaték [Nm]')
    axs[2].legend(loc='upper right')
    axs[2].grid(True)

    axs[3].plot(t_arr, [r['q_curr'] for r in log_data], 'c-', label='Iq Áram [A]')
    axs[3].set_ylabel('Áram [A]')
    axs[3].set_xlabel('Idő [s]')
    axs[3].legend(loc='upper right')
    axs[3].grid(True)

    plt.tight_layout()
    png_file = "teszt_1_pozicio.png"
    plt.savefig(png_file, dpi=150)
    print(f"Grafikon elmentve: {png_file}")
    print(f"Utolsó állapot -> Mód: {log_data[-1]['mode']}, Hibakód (Fault): {log_data[-1]['fault']}")

if __name__ == '__main__':
    asyncio.run(main())