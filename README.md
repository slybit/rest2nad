# REST2NAD

A tiny Python based REST server to control your NAD Receiver (or other equipment) through its RS232 port.
I guess this is only useful for older models (like mine) that do not yet have a built-in ethernet port. But I guarantee you that buying a Raspberry Pi to run this will be much cheaper than getting a new receiver :-)

I run this on my Raspberry Pi based music streamer that sits next to the receiver.

It allows, for example, to make some custom integrations with Home Assistant to control the receiver.

## Config

Just adapt the simple config.yaml file to your needs:
```
serial:
  port: /dev/ttyUSB0
rest:
  bindIP: 0.0.0.0
  port: 3333
```

## Using the REST interface

### GET

| item  | value |
| ----- | -------- |
| URL   | `http://host/nad/<command>` |


Here, command is any of the valid NAD commands that can be used to read the state/value from the receiver.

For example, `http://host/nad/Main.Volume` will return the current volume of the receiver.

The returned value is a verbatim copy of the output from the receiver. For example, `Main.Volume=-40`.

### POST (REST)

| item  | value |
| ----- | -------- |
| URL   | `http://host/nad/<command>` |
| BODY  | plaintext, e.g., `=-40`, `+` or `=On` |

For example, `http://host/nad/Main.Volume` with body `=-40` will set the volume of the receiver to -40dB.

Internally, the command from the URL and the body are simply concatenated before sending it to the receiver over RS232.

Again, the return value is a verbatim copy of the output from the receiver.

### POST (NON-REST)

| item  | value |
| ----- | -------- |
| URL   | `http://host/nad/` |
| BODY  | plaintext, e.g., `Main.Volume=-40` |

For example, `http://host/nad/` with body `Main.Power=On` will turn on the receiver.

Internally, the command is taken verbatim from the body and sent to the receiver over RS232.

Again, the return value is a verbatim copy of the output from the receiver.

## Using the nad.service

Adapt the `nad.service` to your needs. Likely the only thing you would want to change is the location of the nad.py script and the config.yaml file:

```
ExecStart=/usr/bin/python /home/volumio/nad.py /home/volumio/config.yaml
```

### Install the service file

```bash
sudo cp nad.service /etc/systemd/system/nad.service
sudo chmod 644 /etc/systemd/system/nad.service
```

### Use it
```bash
sudo systemctl enable myservice
sudo systemctl start myservice
sudo systemctl status myservice
```
