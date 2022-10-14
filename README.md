# st2g (short for securitytext2graph)
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

## Example
Input:
```
First, /usr/bin/wget will be started by /bin/bash . It downloads some data from 162.125.6.6, then writes the data to sysrep_exp_data.txt.
```

Output:
```
// Default Behaviour Graph
digraph {
	0 [label="/usr/bin/wget" xlabel=LinuxFilepath]
	1 [label="/bin/bash" xlabel=LinuxFilepath]
	2 [label="162.125.6.6" xlabel=IP]
	3 [label="sysrep_exp_data.txt" xlabel=Filename]
	1 -> 0 [label=start xlabel="[0]"]
	0 -> 2 [label=download xlabel="[1]"]
	0 -> 3 [label=write xlabel="[2]"]
}
```
