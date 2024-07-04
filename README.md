# websnap

#### CLI that downloads files from URLs and upload them to S3 bucket. 

Also supports writing downloaded files to local machine. 

[EnviDat](https://www.envidat.ch) is the environmental data portal of the Swiss Federal Institute for Forest, Snow and Landscape Research WSL.

TODO include diagram


## Documentation Topics

> - [Installation](#installation)
> - [CLI Options](#cli-options)
> - [Usage: S3 Bucket](#usage-s3-bucket)
> - [Usage: Local Machine](#usage-local-machine)
> - [Configuration](#configuration)
> - [Scheduled Websnap](#scheduled-websnap)
> - [Pre-commit Hooks](#pre-commit-hooks)
> - [Author](#author)
> - [License](#license)


## Installation

   ```bash
    pip install pdm
    pdm install
   ```


## CLI Options

To access CLI options in terminal execute: `pdm run websnap-cli --help`

TODO document CLI options in table here.


## Usage: S3 Bucket

Download files from URLs and upload them to S3 bucket.

### Commands

TODO document S3 commands here.

### Configuration

TODO document S3 configuration here
TODO document config citing example.ini files


## Usage: Local Machine

### Commands

TODO document local machine commands here

### Configuration

TODO document local machine configuration here

TODO document config citing example.ini files


## Scheduled Websnap

TODO document


## Pre-commit Hooks

- To run the pre-commit hooks manually open app in terminal and execute: `pre-commit run --all-files`
- These hooks ensure that the application uses standard stylistic conventions
- To view or alter the pre-commit hooks see: `.pre-commit-config.yaml`


## Author
[Rebecca Kurup Buchholz](https://www.linkedin.com/in/rebeccakurupbuchholz/), Swiss Federal Institute for Forest, Snow and Landscape Research WSL 


## License

[MIT License](https://gitlabext.wsl.ch/EnviDat/websnap/-/blob/main/LICENSE?ref_type=heads)

