# 🚇 Tube Departure Board for Raspberry Pi

<!--- Start of badges -->
<!-- Badges: python,raspberrypi,api,3d_printing,electronics,tfl -->

<p align="left"><img alt="3D Printing" src="https://img.shields.io/badge/-3D Printing-FF5722.svg?logo=data:image/svg+xml;base64,PHN2ZyB2ZXJzaW9uPSIxLjEiIGlkPSJDYXBhXzEiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiIHg9IjBweCIgeT0iMHB4IgoJIHdpZHRoPSI1My40MTZweCIgaGVpZ2h0PSI1My40MTZweCIgdmlld0JveD0iMCAwIDUzLjQxNiA1My40MTYiIHN0eWxlPSJlbmFibGUtYmFja2dyb3VuZDpuZXcgMCAwIDUzLjQxNiA1My40MTY7IgoJIHhtbDpzcGFjZT0icHJlc2VydmUiPgo8Zz4KCTxnPgoJCTxwYXRoIGQ9Ik0yMC45ODEsMTQuNDF2LTMuODUzYy0xLjA2NCwwLTEuOTI2LDAuODYzLTEuOTI2LDEuOTI2QzE5LjA1NiwxMy41NDcsMTkuOTE3LDE0LjQxLDIwLjk4MSwxNC40MXoiIGZpbGw9IiNGRkZGRkYiLz4KCQk8cGF0aCBkPSJNMzQuMzYsMTIuNDgyYzAtMS4wNjMtMC44NjEtMS45MjYtMS45MjYtMS45MjZ2My44NTNDMzMuNDk5LDE0LjQxLDM0LjM2LDEzLjU0NywzNC4zNiwxMi40ODJ6IiBmaWxsPSIjRkZGRkZGIi8+CgkJPHBhdGggZD0iTTQ5LjMzMywwSDQuMDgzYy0xLjM3OSwwLTIuNSwxLjEyMS0yLjUsMi41djQ4LjQxNmMwLDEuMzc5LDEuMTIxLDIuNSwyLjUsMi41aDQ1LjI1YzEuMzc5LDAsMi41LTEuMTIxLDIuNS0yLjVWMi41CgkJCUM1MS44MzMsMS4xMjEsNTAuNzEyLDAsNDkuMzMzLDB6IE00LjU4MywxMC4xODVoMTcuMDk2djExLjIyM2gzLjQwNHYyLjAzOGMwLDAuMjkzLDAuMDgzLDAuNTY0LDAuMjE3LDAuODAyCgkJCWMtMC4wMzksMC4yNjktMC4wNjcsMC41NDgtMC4wNjcsMC44NDNjMCwxLjI5LDAuOTAzLDIuMzgsMS4zMDQsMi44bC0yLjA2OSwzLjIxM2gtNy42MDF2OC40OThoOC40OTh2LTIuMDg0aDEuODc2CgkJCWMwLjQ2NywxLjQ4NSwxLjYwNywyLjYxNSwzLjAzOSwzLjA4Nkg0LjU4M1YxMC4xODV6IE0yOS4wMzQsMzMuNDQ5bDAuNDMyLTAuMzM4YzAuNjY5LTAuNTI0LDEuNDcxLTAuODAzLDIuMzE2LTAuODAzCgkJCWMyLjA3NiwwLDMuNzY3LDEuNjg5LDMuNzY3LDMuNzY4cy0xLjY4OCwzLjc2Ny0zLjc2NywzLjc2N2MtMS43NzIsMC0zLjI4Mi0xLjIwNy0zLjY3Mi0yLjkzNmwtMC4wODgtMC4zOWgtMy42NTlWMzguNmgtNi40OTgKCQkJdi02LjQ5OGg3LjE0NmwxLjU3OC0yLjQ0N0wyOS4wMzQsMzMuNDQ5eiBNMTkuMDU2LDQ4Ljk0MWMwLDAuNTUyLTAuNDQ4LDEtMSwxaC04Ljk2Yy0wLjU1MywwLTEtMC40NDgtMS0xdi00YzAtMC41NTMsMC40NDctMSwxLTEKCQkJaDguOTZjMC41NTIsMCwxLDAuNDQ3LDEsMVY0OC45NDF6IE00MS4yMDgsNDMuMDgzaC0zLjI1di0xaDMuMjVWNDMuMDgzeiBNNDUuOTU4LDQzLjA4M2gtMy4yNXYtMWgzLjI1VjQzLjA4M3ogTTQ4LjgzMyw0MC42MDQKCQkJSDMzLjIwMWMxLjkzMy0wLjYwOCwzLjM0OC0yLjM5NiwzLjM0OC00LjUyN2MwLTIuNjI4LTIuMTM4LTQuNzY4LTQuNzY3LTQuNzY4Yy0wLjg4OSwwLTEuNzM4LDAuMjQxLTIuNDg1LDAuNzAybC0yLjU0NS0zLjk1CgkJCWMwLjEyNy0wLjExNywxLjQ3Mi0xLjM5NiwxLjQ3Mi0yLjk3MWMwLTAuMjk2LTAuMDI3LTAuNTc2LTAuMDY3LTAuODQ2YzAuMTM0LTAuMjM4LDAuMjE2LTAuNTA4LDAuMjE2LTAuOHYtMi4wMzhoMy40MDZWMTAuMTg1CgkJCWgxNy4wNTVWNDAuNjA0eiBNNDguODMzLDguNjVIMzEuNzc4VjUuODI1aC0xMC4xVjguNjVINC41ODNWM2g0NC4yNVY4LjY1eiIgZmlsbD0iI0ZGRkZGRiIvPgoJPC9nPgo8L2c+Cjwvc3ZnPg==&style=flat-square" /> <img alt="Api" src="https://img.shields.io/badge/-API-007ACC.svg?logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPCEtLSBMaWNlbnNlOiBNSVQuIE1hZGUgYnkgR2l0bGFiOiBodHRwczovL2dpdGxhYi5jb20vZ2l0bGFiLW9yZy9naXRsYWItc3Zncz9yZWY9aWNvbmR1Y2suY29tIC0tPgo8c3ZnIHdpZHRoPSI4MDBweCIgaGVpZ2h0PSI4MDBweCIgdmlld0JveD0iMCAwIDE2IDE2IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxwYXRoIGZpbGwtcnVsZT0iZXZlbm9kZCIgY2xpcC1ydWxlPSJldmVub2RkIiBkPSJNOS4yNTMgMi43ODJsLTEuMTEtLjI3M2E0LjAyMSA0LjAyMSAwIDAwLS41OTMgMS4wMjVsLjc5LjgyNWEzLjAwNSAzLjAwNSAwIDAwMCAxLjI4MmwtLjc5LjgyNWMuMTQ3LjM3Mi4zNDguNzE3LjU5MyAxLjAyNWwxLjExLS4yNzNjLjMxNS4yODguNjkzLjUwOSAxLjEwOS42NDFsLjMxOCAxLjA5N2EzLjk5OSAzLjk5OSAwIDAwMS4xODUgMGwuMzE4LTEuMDk3YTIuOTg1IDIuOTg1IDAgMDAxLjExLS42NDFsMS4xMS4yNzNjLjI0NS0uMzA4LjQ0Ni0uNjUzLjU5My0xLjAyNWwtLjc5Mi0uODI1YTMuMDA1IDMuMDA1IDAgMDAwLTEuMjgybC43OTItLjgyNWE0LjAyMSA0LjAyMSAwIDAwLS41OTMtMS4wMjVsLTEuMTEuMjczYTIuOTg1IDIuOTg1IDAgMDAtMS4xMS0uNjQxbC0uMzE4LTEuMDk3YTMuOTg1IDMuOTg1IDAgMDAtMS4xODUgMGwtLjMxOCAxLjA5N2EyLjk4MiAyLjk4MiAwIDAwLTEuMTEuNjQxek0xMi4yNzMgNWExIDEgMCAxMS0yIDAgMSAxIDAgMDEyIDB6IiBmaWxsPSIjZmZmZmZmIi8+CiAgPHBhdGggZmlsbC1ydWxlPSJldmVub2RkIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik02LjkxNSA2LjI2NEE0LjU0IDQuNTQgMCAwMDUuNyA2LjA0bC0uNDQ1LjkxOGEzLjU4OCAzLjU4OCAwIDAwLTEuMzY0LjM3bC0uODUtLjU2NGMtLjM0NS4yMjYtLjY2LjQ5OS0uOTMyLjgxbC40NC45MmMtLjI3LjM5MS0uNDYyLjgzMy0uNTYgMS4yOThsLS45NzEuMzEyYTQuNTEgNC41MSAwIDAwLjA1MSAxLjIzM2wuOTk1LjIzYy4xMzYuNDU2LjM2My44OC42NjUgMS4yNDhsLS4zNjIuOTU0Yy4yOTguMjg3LjYzMi41MzIuOTk2LjcyOGwuOC0uNjMzYTMuNTggMy41OCAwIDAwMS4zOS4yNTdsLjUyMS44NzdjLjQwOS0uMDUzLjgxLS4xNjIgMS4xOS0uMzI0bC4wMDQtMS4wMmEzLjU4IDMuNTggMCAwMDEuMDY3LS45MjdsMS4wMS4xNGMuMjE1LS4zNTMuMzgtLjczNS40OS0xLjEzM2wtLjc5Ni0uNjM5YTMuNjEgMy42MSAwIDAwLS4wNTgtMS40MTNsLjczOS0uNzAxYTQuNTA4IDQuNTA4IDAgMDAtLjU4MS0xLjA5bC0uOTk1LjIyNGEzLjU4OCAzLjU4OCAwIDAwLTEuMTQxLS44MzRsLS4wODgtMS4wMTd6bS0xLjE1IDIuODJhMS40NzcgMS40NzcgMCAxMS0uNTM4IDIuOTA0IDEuNDc3IDEuNDc3IDAgMDEuNTM5LTIuOTA1eiIgZmlsbD0iI2ZmZmZmZiIvPgo8L3N2Zz4=&style=flat-square" /> <img alt="Electronics" src="https://img.shields.io/badge/-Electronics-2E7D32.svg?style=flat-square&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0naXNvLTg4NTktMSc/Pgo8IS0tIExpY2Vuc2U6IENDMC4gTWFkZSBieSBTVkcgUmVwbzogaHR0cHM6Ly93d3cuc3ZncmVwby5jb20vc3ZnLzE3MjE4MC9jZWxsIC0tPgo8c3ZnIHZlcnNpb249IjEuMSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB2aWV3Qm94PSIwIDAgMjk4IDI5OCIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiIGVuYWJsZS1iYWNrZ3JvdW5kPSJuZXcgMCAwIDI5OCAyOTgiPgogIDxnIGZpbGw9IiNmZmZmZmYiPgogICAgPHBvbHlnb24gcG9pbnRzPSIyOTgsMTQxIDE4MiwxNDEgMTgyLDExNiAxNjYsMTE2IDE2NiwxODIgMTgyLDE4MiAxODIsMTU3IDI5OCwxNTcgICIvPgogICAgPHBvbHlnb24gcG9pbnRzPSIxMTYsMTQxIDAsMTQxIDAsMTU3IDExNiwxNTcgMTE2LDIxNSAxMzIsMjE1IDEzMiw4MyAxMTYsODMgICIgLz4KICA8L2c+Cjwvc3ZnPgo=" /> <img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white&style=flat-square" /> <img alt="Raspberrypi" src="https://img.shields.io/badge/-Raspberry%20Pi-C51A4A?logo=raspberry-pi&logoColor=white&style=flat-square" /> <img alt="Tfl" src="https://img.shields.io/badge/-TfL-000f9f.svg?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjRweCIgaGVpZ2h0PSIyNHB4IiB2aWV3Qm94PSIwIDAgMjQgMjQiIHJvbGU9ImltZyIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDx0aXRsZT5UcmFuc3BvcnQgZm9yIExvbmRvbiBpY29uPC90aXRsZT4KICAgIDxwYXRoIGZpbGw9IiNmZmZmZmYiIGQ9Ik0xMiAyLjI1YTkuNzMgOS43MyAwIDAgMC05LjQ5IDcuNUgwdjQuNWgyLjUxYTkuNzMgOS43MyAwIDAgMCA5LjQ5IDcuNWM0LjYyIDAgOC40OC0zLjIgOS40OS03LjVIMjR2LTQuNWgtMi41MUE5LjczIDkuNzMgMCAwIDAgMTIgMi4yNXpNMTIgNmMyLjUgMCA0LjY2IDEuNTYgNS41NiAzLjc1SDYuNDRBNi4wMiA2LjAyIDAgMCAxIDEyIDZ6bS01LjU2IDguMjVoMTEuMTJBNi4wMiA2LjAyIDAgMCAxIDEyIDE4YTYuMDIgNi4wMiAwIDAgMS01LjU2LTMuNzVaIiAvPgo8L3N2Zz4=&logoColor=white&style=flat-square" /></p>
<!--- End of badges -->

![Miniature Tube Departure Board](Images/banner.jpg)

Recreate the iconic London Underground departure board with a Raspberry Pi! This Python-based application fetches live train data from the Transport for London (TfL) Unified API and displays it in real-time on a compact OLED screen, designed to mimic the classic dot-matrix look. 

### Table of Contents

**[✨ Features](#-features) <br> 
[📋 Prerequisites](#-prerequisites) <br>
[🔌 Raspberry Pi Setup](#-raspberry-pi-setup) <br>
[🔧 Hardware Assembly and Wiring](#-hardware-assembly-and-wiring) <br>
[💻 Software Installation](#-software-installation) <br>
[🙏 Credits & Inspiration](#-credits--inspiration)**

<br>

## ✨ Features

- **Live London Underground Data:** Fetches real-time Tube arrival predictions for configurable stations and lines.

- **Dot-Matrix Aesthetics:** Utilises a [Dot Matrix Typeface](https://github.com/DanielHartUK/Dot-Matrix-Typeface) to give your display an authentic departure board feel.

- **Compact Display:** Designed for an SSD1322 OLED display on Raspberry Pi.

- **Dual Line Toggle:** Switch between two sets of Tube lines/directions using a physical toggle switch.

- **Smart Power Management:** Includes Raspberry Pi temperature monitoring to prevent overheating.

- **Multi-threaded Architecture:** Uses separate threads for API fetching and display rendering to ensure smooth, responsive updates.

- **Custom 3D-Printed Case:** Design files provided for a miniature Tube departure board enclosure.

## 📋 Prerequisites

To build your London Underground Departure Board, you'll need the following:

- **Raspberry Pi:** Any model capable of running Raspberry Pi OS. I personally used a [Pi Zero WH](https://thepihut.com/products/raspberry-pi-zero-wh-with-pre-soldered-header?variant=547332849681&country=GB&currency=GBP&utm_medium=product_sync&utm_source=google&utm_content=sag_organic&utm_campaign=sag_organic&gad_source=1&gad_campaignid=11284298573&gbraid=0AAAAADfQ4GGELxyUDK-MXwh7vph4BEDCa&gclid=Cj0KCQjw1JjDBhDjARIsABlM2SsFhuRp0j_vZ-WN3Cg39v57Ki52kaFcM2Zpd7_jJAu70MgbLrW5hQMaAmodEALw_wcB).

- **Micro SD card:** For installing the Raspberry Pi OS.

- **Internet Connection:** For the Raspberry Pi to access the TfL API.

- **OLED Display:** An [SSD1322-based OLED display module](https://www.ebay.co.uk/itm/265720175865) connected via SPI.

- **Toggle Switch (Optional but Recommended):** A [mini toggle switch](https://www.amazon.co.uk/dp/B077D9FRGL?ref=ppx_pop_mob_ap_share) connected to a GPIO pin on your Raspberry Pi to switch between the two line configurations (e.g. westbound and eastbound).

- **Transport for London (TfL) API Key:** Tube arrival data is fetched from the [Transport for London Unified API](https://api.tfl.gov.uk/).

- **Access to a 3D printer:** STL files for the custom case, designed to resemble a miniature tube departure board, are provided within this repository.

- **8x [5mmx2mm magnets](https://www.amazon.co.uk/dp/B09H2W3TQZ?ref=ppx_pop_mob_ap_share):** For mounting the miniature departure board.

- **4x M2.6x8mm self tapping screws:** To secure the display and Raspberry Pi to the case.

- **2 x M2.6x6mm self tapping screws:** For closing the case with the back cover.

- **Superglue:** For assembling some of the 3D-printed parts and securing the magnets.

- **Wires and soldering equipment:** For connecting the display and switch to your Raspberry Pi.

## 🔌 Raspberry Pi Setup

These steps prepare your Raspberry Pi's operating system for the project.

### 1. Flash Raspberry Pi OS

- Download the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) for your computer
- Use the Imager to flash Raspberry Pi OS onto your Micro SD card with the following OS customisation settings:
  - **Enable SSH** with password authentication (under the 'Services' tab). This is essential for connecting to your Pi remotely.
  - **Set a username and password.** Make a note of these; you'll need them for SSH access.
  - **Configure wireless LAN.** Add your SSID (Wi-Fi network name) and password.
  - **Set up the locale settings** with the `Europe/London` timezone.
- Insert the prepared SD card into your Raspberry Pi.

### 2. Connect to your Raspberry Pi

- The Raspberry Pi receives its power through its Micro USB Power port. Connect a standard 5V power supply to this port. *Note: On the Pi Zero WH, this is typically the port closest to the end of the board, distinct from any data-only USB ports.*

- Find your Pi's IP address (e.g., from your router's connected devices list) and connect via SSH from your computer:

    ```
    ssh <your_username>@<your_pi_ip_address>
    # Use the username and password you set in the Imager.
    ```

### 3. Enable SPI interface:

For your SSD1322 OLED, you'll need to enable the SPI interface on your Raspberry Pi.

- Open the Raspberry Pi Configuration tool:

    ```
    sudo raspi-config
    ```
- Navigate to `Interface Options` -> `SPI` -> `Yes` to enable it.

- Select `Finish` and reboot your Pi if prompted.

## 🔧 Hardware Assembly and Wiring

This section guides you through preparing the 3D-printed case and connecting your components.

### **1. Wiring:**

The SSD1322 OLED display is wired to the Raspberry Pi by following the comprehensive instructions found in [Chris Crocker-White's UK national rail departure display](https://github.com/chrisys/train-departure-display/blob/main/docs/02-connecting-the-display-to-the-pi.md).

Additionally, a toggle switch has been integrated into this project. This switch enables the display to cycle between different sets of arrival information (for example, distinguishing between eastbound and westbound trains, or various platforms). It is set up in a pull-down configuration, as shown in the provided diagram:

- Connect the centre terminal of the switch to a 3.3V power pin on the Raspberry Pi (e.g., physical pin 17).

- Connect one of the outer terminals of the switch to a Raspberry Pi GPIO pin (e.g. GPIO17, physical pin 11).

- Connect a ~10k Ohm resistor between the Raspberry Pi GPIO pin and a ground pin on the Raspberry Pi. This resistor acts as a pull-down, ensuring the GPIO pin is held low when the switch is open.

      +--------------- (Raspberry Pi 3.3V Power Pin)
      |
      |
      |   +--------------------+
      |   |                    |
      |   |      (Switch)      |
      |   |                    |
      |   +--------------------+
      |             |          |
      |        (Centre Pin) (Outer Pin)
      |             |          |
      +-------------+          |
                               |
                               +------------ Raspberry Pi GPIO Pin
                               |
                               |
                        [ 10kΩ Resistor ]
                               |
                               |
                               | 
                   Raspberry Pi Ground Pin

### **2. 3D Print the Case:**

3D print the [STL files](3D_print_files) provided in this repository. I printed the parts using black PLA filament on an Ender 3 printer.

To give a quick overview, the 3D-printed case consists of the following parts, designed to assemble into a compact and functional departure board:

![3D printed parts illustration](Images/3D_printed_parts.jpg)

- **Case-main:** The primary rectangular enclosure featuring a cutout at the front for securely fitting the OLED display. Its open rear is designed to be covered by the `case-back` panel.

- **Case-back:** A flat panel that forms the rear closure of the `case-main`, attaching securely with self-tapping screws.

- **Pole (x2):** Two hollow, elliptical posts designed to be superglued to the top of the `case-main`. They align with an elliptical opening on the `case-main`'s top surface, allowing the Raspberry Pi's Micro USB power cable to pass through them. The top of each pole is designed to house two 5mm diameter magnets for mounting the assembled board.

- **Pole-fixture (x2):** Two flat, elliptical parts that are intended to be permanently glued/taped to the desired mounting surface (designed for an overhang). Each `pole-fixture` is designed to hold two 5mm diameter magnets, enabling the departure board's poles to magnetically attach and detach.

- **Internal-structure:** This component fits inside the `case-main`. It features four integrated mounting posts that align with the Raspberry Pi's screw holes, allowing the Pi to be mounted to it. The Pi is secured by heat-staking the posts (gently melting them with a soldering iron), a technique inspired by [Chris Crocker-White's design](https://github.com/chrisys/train-departure-display/blob/main/docs/03-assembling-the-case.md). The `internal-structure` then sits on top of the OLED display, and both are secured into the `case-main` using four self-tapping screws at each corner. It also incorporates a rectangular strut designed for clamping the toggle switch.

### 3. Assemble everything!
![Assembly illustration](Images/assembly.gif)

***Important Pre-Assembly Note:** After securing the switch to the `internal-structure` and placing the Raspberry Pi, it becomes difficult or impossible to insert the Micro SD card. Therefore, ensure you complete the "Flash Raspberry Pi OS" step (Step 1 in the Raspberry Pi Setup section) and insert the prepared SD card into your Raspberry Pi before proceeding with the full assembly steps below.*

Follow these steps to assemble your departure board:

- **Prepare magnets & poles:**
Superglue the 5mm diameter magnets into the designated holes in both the `pole` and `pole-fixture` parts. Ensure you get the polarity right so that the poles on the departure board attract, rather than repel, the magnets in the fixture!
Superglue the `poles` onto the top surface of the `case-main`, aligning them with the elliptical openings.

- **Mount Raspberry Pi & switch:**
Position the Raspberry Pi on the four struts of the `internal-structure` and secure it in place by heat-staking the struts (gently melting them with a soldering iron to secure the Pi's mounting holes). Clamp the toggle switch onto the rectangular strut of the `internal-structure` using the bolt that usually comes with the toggle switch.

- **Position display:**
Carefully position the display over the front opening of the `case-main`.

- **Assemble case with electronics:**
Place the `internal-structure`(with the Raspberry Pi and toggle switch now attached) into the `case-main`, resting it on top of the display. Secure both the display and `internal-structure` to the `case-main` using 4x M2.6x8mm self-tapping screws, one in each corner.

- **Connect Micro USB power:**
Connect the Micro USB cable to your Raspberry Pi's power port, carefully threading it through the hollow pole that aligns with the power port.

- **Final enclosure:**
Arrange all wires neatly inside the case.
Secure the back panel (`case-back`) to the `case-main` with 2x M2.6x6mm self-tapping screws.

## 💻 Software Installation

These steps cover obtaining the project code, installing software dependencies, and configuring the application.

### 1. Clone the GitHub repository:

- From your Raspberry Pi's terminal, navigate to where you want to store the project (e.g., your home directory `cd ~`) and clone the repository:

    ```
    cd ~
    git clone https://github.com/isi22/Tube-Departure-Board
    cd Tube-Departure-Board
    ```

### 2. Create a python virtual environment:
Using a virtual environment is best practice for managing project dependencies.

```
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install system and python dependencies:
Install system dependencies (for fonts and display drivers and all required Python packages from the `requirements.txt`.

```
sudo apt-get install -y python3-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7 build-essential pkg-config

pip install -r requirements.txt
```

### 4. Configure the project settings:

Update the `config.py` file with your project-specific configurations. This is where you define your station, the lines to monitor, and settings for your OLED and optional GPIO switch.

- Open the file:
    ```
    nano src/config.py
    ```

- Once `nano` opens, you will see the contents of `config.py`. Use the arrow keys to move the cursor up, down, left, and right. Type directly to make your changes.

- Save and Exit (`Ctrl + X`).

### 5. Set up the main script as a systemd service:

To ensure the departure board starts automatically when your Raspberry Pi boots and runs reliably in the background, set it up as a systemd service.

- Create a systemd service file:
    ```
    sudo nano /etc/systemd/system/tube-departure-board.service
    ```

- Add the following content to the file. Replace `<your_username>` and `<your_api_key>` with your actual username and API credentials. The TfL API Key (referred to as primary key) can be found in your [Profile](https://api-portal.tfl.gov.uk/profile) in the TfL API portal after registering and subscribing to the `500 Requests per min` product.

    ```
    [Unit]
    Description=London Underground Departure Board Service
    After=network.target

    [Service]
    User=<your_username>
    WorkingDirectory=/home/<your_username>/Tube-Departure-Board
    ExecStart=/home/<your_username>/Tube-Departure-Board/.venv/bin/python /home/<your_username>/Tube-Departure-Board/src/main.py
    Restart=on-failure
    StandardOutput=journal
    StandardError=journal
    Environment = "TFL_API_KEY=<your_api_key>"
    
    [Install]
    WantedBy=multi-user.target
    ```

- Save and exit (Ctrl+O, Enter, Ctrl+X in nano).

- Reload systemd, enable, and start the service:

    ```
    sudo systemctl daemon-reload
    sudo systemctl enable tube-departure-board.service
    sudo systemctl start tube-departure-board.service
    ```

- Check the service status and logs:

    ```
    sudo systemctl status tube-departure-board.service
    journalctl -u tube-departure-board.service -f # For live service logs
    ```

- Confirm that the service is active (running).

## 🙏 Credits & Inspiration

This project draws inspiration and direct resources from the following:

- **Dot Matrix Typeface:** The authentic visual style is achieved using [Daniel Hart's](https://github.com/DanielHartUK/Dot-Matrix-Typeface) excellent Dot Matrix Typeface.

- **Core Code & Logic:** Both [Chris Crocker-White's](https://github.com/chrisys/train-departure-display) UK National Rail Departure Display and [Sean Petykowski's](https://github.com/petykowski/London-TFL-Arrivals-Board) London TfL Arrivals Board served as direct inspiration and a foundational basis for the Python code and API interaction logic implemented in this project.

- **Hardware Design, Assembly & 3D Printed Parts:**
[Chris Crocker-White's](https://github.com/chrisys/train-departure-display) comprehensive documentation for his UK National Rail Departure Display was particularly instrumental for the hardware design, assembly techniques (such as heat-staking the Raspberry Pi into the case), and provided significant inspiration for the custom 3D-printed enclosure parts. His detailed wiring guide for the display was also followed.


