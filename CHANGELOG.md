# CHANGELOG

## 2.0.7 (2025-05-02)
### Docs
- reformat README summary messages 

## 2.0.6 (2025-03-05)
### Docs
- update license copyright

## 2.0.5 (2025-03-05)
### Docs
- update README badges

## 2.0.4 (2025-02-28)
### Docs
- update README S3 usage examples 

## 2.0.3 (2025-02-25)
### Docs
- update README and metadata reference links 

## 2.0.2 (2025-02-24)
### Docs
- update metadata classifiers

## 2.0.1 (2025-02-24)
### Tests
- implement automated tox tests for the following Python versions: 3.11, 3.12, 3.13
### Docs
- add supported versions badge to README 
- add Python 3.13 to metadata classifiers

## 2.0.0 (2024-09-12)
### Refactor
- process S3 credentials with environment variables rather than in a configuration file
### Docs
- update README to include S3 environment variables explanation


## 1.3.7 (2024-09-11)
### Refactor
- update dependencies

## 1.3.6 (2024-09-11)
### Refactor
- improve arguments validation call

## 1.3.5 (2024-09-11)
### Refactor
- improve error handling and arguments validation
- modify tests to cover refactored error handling

## 1.3.4 (2024-09-09)
### Docs
- add black badge
- implement collapsible sections to improve readability of README

## 1.3.3 (2024-09-08)
### Tests
- increase test coverage 

## 1.3.2 (2024-09-04)
### Tests
- implement pytest tests and fixtures

## 1.3.1 (2024-08-30)
### Docs
- add JSON config template files
- add links to JSON config template files in README

## 1.3.0 (2024-08-30)
### Feat
- add `section_config` argument that allows optional additional configuration sections
- `section_config` can be a URL or a path to a JSON configuration file
### Docs
- add `section_config` description and limitations to options table 

## 1.2.11 (2024-08-20)
### Refactor
- improve validation for integer arguments
### Docs
- add parameter data types in description table

## 1.2.10 (2024-08-16)
### Docs
- update function code snippet examples

## 1.2.9 (2024-08-15)
### Refactor
- extract repeat_minutes arg logic to helper function
### Docs
- reformat function parameters table
- add keywords to project metadata in `pyproject.toml`

## 1.2.8 (2024-08-14)
### Docs
- update pypi badge link

## 1.2.7 (2024-08-14)
### Docs
- remove unused `black` dependency

## 1.2.6 (2024-08-14)
### Docs
- update download badge link

## 1.2.5 (2024-08-14)
### Docs
- update badge formatting

## 1.2.4 (2024-08-14)
### Docs
- add version, download, and license badges
- update config templates to show .xml examples

## 1.2.3 (2024-08-13)
### Docs
- update overview diagram
- correct CHANGELOG date

## 1.2.2 (2024-08-13)
### Refactor
- update dev-dependencies
- improve README descriptions and usage instructions

## 1.2.1 (2024-08-13)
### Refactor
- improve boto3 S3 ClientError handling 

## 1.2.0 (2024-08-13)
### Feat
- implement `timeout` argument that is the number of seconds to wait for response for 
  each HTTP request before timing out
### Docs
- update README to include usage and default value for `timeout` argument

## 1.1.12 (2024-08-12)
### Fix
- correct classifiers

## 1.1.11 (2024-08-12)
### Fix
- remove invalid classifier

## 1.1.10 (2024-08-12)
### Docs
- add additional classifiers

## 1.1.9 (2024-08-12)
### Docs
- improve project description and README

## 1.1.8 (2024-08-08)
### Docs
- remove internal README links that are not supported by PyPI

## 1.1.7 (2024-08-08)
### Docs
- add hyperlinks to README

## 1.1.6 (2024-08-07)
### CI
- refactor package publishing stage

## 1.1.5 (2024-08-07)
### Docs
- improve README

## 1.1.4 (2024-08-07)
### CI
- test automated package publishing

## 1.1.3 (2024-08-07)
### Docs
- improve project description

## 1.1.2 (2024-08-07)
### Fix
- remove automated pip-package CI stage

## 1.1.1 (2024-08-07)
### Docs
- improve docs overview diagram image

## 1.1.0 (2024-08-07)
### Feat
- add support for using websnap as a function
- automate pypi package deployment

## 1.0.0 (2024-07-15)
### Feat
- initial release of websnap CLI
