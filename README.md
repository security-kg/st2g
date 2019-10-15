# securitytext2graph
Covert security articles to graph representations

## How to install
```
apt-get install graphviz  # for ubuntu, similar command for other platform
pip3 install -e .
python3 -m spacy download en_core_web_sm
```

## How to use
```
st2g -i <input_file_path> -o <output_file_path>
```
or if you're using the source code:
```
python3 src/st2g/main.py -i <input_file_path> -o <output_file_path>
```