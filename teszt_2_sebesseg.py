# Teszt 2: Sebesség- és gyorsulásprofil

import asyncio
import time
import csv
import math
import moteus
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

async def main():
    qr = moteus.QueryResolution()
    qr.q_current = moteus.F32
    qr.temperature = moteus.F32
    qr._extra = {
        moteus.Register.CONTROL_VELOCITY: moteus.F32,
        moteus.Register.VOLTAGE: moteus.F32,
        moteus.Register.FAULT: moteus.INT8,
    }

    c = moteus.Controller(id=1, query_resolution=qr)

    state = await c.set_stop(query=True)
    print("2. Teszt: Sebesség- és gyorsulásprofil indul (5 másodperc)...")

    log_data = []
    t0 = time.monotonic()

    try:
        while True:
            t = time.monotonic() - t0
            if t > 5.0:
                break

            # Sebességlépcsők definiálása
            if t < 0.5:
                target_vel = 0.0
            elif t < 2.0:
                target_vel = 3.0   # +3 fordulat/mp előre
            elif t < 3.5:
                target_vel = -2.0  # -2 fordulat/mp hátra
            else:
                target_vel = 0.0   # Megállás

            # Tiszta sebességvezérlés: position=math.nan !
            state = await c.set_position(
                position=math.nan,
                velocity=target_vel,
                accel_limit=4.0,        # 4 rev/s^2 gyorsulási rámpa
                maximum_torque=0.5,     # 0.5 Nm nyomatékkorlát
                query=True
            )

            v = state.values
            log_data.append({
                'time': t,
                'pos': v.get(moteus.Register.POSITION, 0.0),
                'raw_target_vel': target_vel,
                'cmd_vel': v.get(moteus.Register.CONTROL_VELOCITY, 0.0),
                'vel': v.get(moteus.Register.VELOCITY, 0.0),
                'torque': v.get(moteus.Register.TORQUE, 0.0),
                'q_curr': v.get(moteus.Register.Q_CURRENT, 0.0),
                'fault': v.get(moteus.Register.FAULT, 0)
            })

            await asyncio.sleep(0.01)

    finally:
        await c.set_stop()
        print("Motor biztonságosan leállítva.")

    # CSV mentés
    csv_file = "teszt_2_sebesseg.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=log_data[0].keys())
        writer.writeheader()
        writer.writerows(log_data)

    # Grafikon generálása
    t_arr = [r['time'] for r in log_data]
    fig, axs = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    fig.suptitle('Moteus C1 + mj5208 - 2. Teszt: Sebesség- és Gyorsulásprofil (position=NaN)', fontsize=14)

    axs[0].plot(t_arr, [r['raw_target_vel'] for r in log_data], 'k:', label='Kért sebességlépcső')
    axs[0].plot(t_arr, [r['cmd_vel'] for r in log_data], 'r--', label='Belső rámpa (accel_limit=4)')
    axs[0].plot(t_arr, [r['vel'] for r in log_data], 'g-', label='Valós sebesség')
    axs[0].set_ylabel('Sebesség [rev/s]')
    axs[0].legend(loc='upper right')
    axs[0].grid(True)

    axs[1].plot(t_arr, [r['pos'] for r in log_data], 'b-', label='Megtett pozíció')
    axs[1].set_ylabel('Pozíció [rev]')
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
    png_file = "teszt_2_sebesseg.png"
    plt.savefig(png_file, dpi=150)
    print(f"Kész! Grafikon: {png_file} | Hibakód: {log_data[-1]['fault']}")

if __name__ == '__main__':
    asyncio.run(main())