<h1 align="center">
  <br>
  <a href="https://purpleops.app"><img src="static/images/logo.png" alt="PurpleOps Logo" width="200"></a>
  <br>
  PurpleOps
  <br>
</h1>

<h4 align="center">An open-source self-hosted purple team management web application.</h4>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licence-blue?logo=unlicense&logoColor=white">
  <a href="https://docs.purpleops.app"><img src="https://img.shields.io/badge/Docs-blue?logo=readthedocs&logoColor=white">
</p>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#credits">Credit</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <img src="static/images/demo.gif">
</p>

## Key Features

* Template engagements and testcases
* Framework friendly
* Role-based Access Control & MFA
* Inbuilt DOCX reporting + custom template support

How PurpleOps is different:

* No attribution needed
* Hackable, no "no-reversing" clauses
* No over complications with tomcat, redis, manual database transplanting and an obtuce permission model

## Installation

```bash
# Clone this repository
$ git clone https://github.com/CyberCX-STA/PurpleOps

# Go into the repository
$ cd PurpleOps

# Alter PurpleOps settings
$ nano .env

# Run the app with docker
$ sudo docker compose up -d

# Alternatively
$ sudo docker run --name mongodb -d -p 27017:27017 mongo
$ pip3 install -r requirements.txt
$ python3 seeder.py
$ python3 purpleops.py
```

## Credits

- Atomic Red Team [(LICENSE)](https://github.com/redcanaryco/atomic-red-team/blob/master/LICENSE.txt) for sample commands
- [CyberCX](https://cybercx.com.au/) for foundational support

## License

Apache