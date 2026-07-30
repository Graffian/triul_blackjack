# Triul Blackjack Bot

Automation bot for the Triumph Blackjack 21 game using seed detection and WebDriverAgent.

## Files

- `mitm-addon.py` — mitmproxy addon that extracts the game seed from API responses
- `calibrate.py` — calibrates tap positions for your iPhone screen
- `play_blackjack.py` — main automation script: reads seed, runs solver, taps via WDA

## Usage

1. **Calibrate**: `python3 calibrate.py`
2. **Start proxy**: `mitmweb -s mitm-addon.py --listen-port 8080`
3. **Run bot**: `python3 play_blackjack.py --wait`
4. **Play the game** on iPhone through the proxy
