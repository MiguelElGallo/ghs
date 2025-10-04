# idea

ghs is a CLI tool to sync your .env files with Github Secrets in both directions. for now it only supports syncing to repositories secrets: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-a-repository 

## Commands 

The first command is testconf in which it will do a simple test to see if it can create a secret and then read it back. The secret will be called ghs_test_secret_<random_string>    and will be deleted after the test.

The second command is get which will get all the secrets from the repository and write them to a .env file. by default it will write to .env but you can specify a different file with the -f flag.

The third command is set which will read a .env file and set the secrets in the repository. by default it will read from .env but you can specify a different file with the -f flag.

## Authentication

Make sure testconf checks the gh CLI tool is installed and authenticated. You can do this by running `gh auth login` and following the prompts.






