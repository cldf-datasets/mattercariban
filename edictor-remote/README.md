# Opening the data in EDICTOR

## Installing packages

Please follow along the tutorial here: <https://github.com/digling/edictor/blob/master/README.md>

Do not hesitate to contact me in case you have questions or something in the tutorial is not working as intended.

Once you have installed EDICTOR3, simply run the `edictor server` command within this folder and enter your username and password.

## Creating the SQLite for Upload

```shell
pip install "edictor[lingpy]"
edictor wordlist --name=mattercariban --sqlite --namespace='{"language_name": "doculect", "concept_name": "concept","value": "value", "form":"form", "segments": "tokens","comment": "note"}' --addon="cognacy:cogid","alignment:alignment"`
```
