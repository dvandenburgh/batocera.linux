#!/usr/bin/python3

import gpiod
from gpiod.line import Bias, Edge, Direction, Value
import os
from datetime import timedelta
import subprocess

# Pin Configuration
POWER_CHIP = "/dev/gpiochip0"
POWER_PIN = 3  # pin 5
LED_PIN = 14   # TXD - pin 8
RESET_PIN = 2  # pin 3
POWEREN_PIN = 4  # pin 7

def init_gpio():
    try:
        gpiod.request_lines(POWER_CHIP,
            config={
                LED_PIN: gpiod.LineSettings(
                    direction=Direction.OUTPUT, 
                    output_value=Value.ACTIVE
                ),
                POWEREN_PIN: gpiod.LineSettings(
                    direction=Direction.OUTPUT, 
                    output_value=Value.ACTIVE
                )
            }
        )
        print("GPIO initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize GPIO: {e}")
        exit(1)

def handle_gpio_event(event_line_offset):
    if event_line_offset == RESET_PIN:
        print("RESET button pressed")
        try:
            output = int(subprocess.check_output(['batocera-es-swissknife', '--espid']))
            output_rc = int(subprocess.check_output(['batocera-es-swissknife', '--emupid']))
            
            if output_rc:
                subprocess.run("batocera-es-swissknife --emukill", shell=True, check=True)
            elif output:
                subprocess.run("batocera-es-swissknife --restart", shell=True, check=True)
            else:
                subprocess.run("reboot", shell=True, check=True)
        except Exception as e:
            print(f"Reset command error: {e}")
    
    elif event_line_offset == POWER_PIN:
        print("POWER button pressed")
        try:
            output = int(subprocess.check_output(['batocera-es-swissknife', '--espid']))
            if output:
                subprocess.run("batocera-es-swissknife --reboot", shell=True, check=True)
            else:
                subprocess.run("reboot", shell=True, check=True)
        except Exception as e:
            print(f"Poweroff command error: {e}")

def watch_gpio_events():
    try:
        with gpiod.request_lines(
            POWER_CHIP,
            config={
                POWER_PIN: gpiod.LineSettings(
                    edge_detection=Edge.FALLING,
                    bias=Bias.PULL_UP,
                    debounce_period=timedelta(milliseconds=1000)
                ),
                RESET_PIN: gpiod.LineSettings(
                    edge_detection=Edge.RISING,
                    bias=Bias.PULL_UP,
                    debounce_period=timedelta(milliseconds=50)
                )
            },
        ) as request:
            print("GPIO event monitoring started")
            for event in request.read_edge_events():
                handle_gpio_event(event.line_offset)
    except Exception as e:
        print(f"Error watching GPIO events: {e}")
        exit(1)

def main():
    init_gpio()
    while True:
        watch_gpio_events()

if __name__ == "__main__":
    main()
