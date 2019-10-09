# securitytext2graph
Covert security articles to graph representations

## How to install
```
pip3 install -e .
python3 -m spacy download en_core_web_sm
```

## How to use
```
python3 src/st2g/main.py -i <input_file_path> -o <output_file_path>
```