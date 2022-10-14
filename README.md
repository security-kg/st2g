# st2g

st2g (short for "securitytext2graph") is an NLP tool that extracts threat behaviors (IOCs and their relations) from text and converts the extracted information into a structured graph representation.

st2g leverages and extends the rules from [ioc_parser](https://github.com/armbues/ioc_parser) to extract IOCs, and leverages dependency parsing to extract IOC relations.

st2g is part of our [ThreatRaptor](https://github.com/seclab-vt/threatraptor) system published in ICDE 2021.

If you use or extend our work, please cite the following paper:

```txt
@inproceedings {gao2021enabling,
 title = {Enabling Efficient Cyber Threat Hunting With Cyber Threat Intelligence},
 author={Gao, Peng and Shao, Fei and Liu, Xiaoyuan and Xiao, Xusheng and Qin, Zheng and Xu, Fengyuan and Mittal, Prateek and Kulkarni, Sanjeev R and Song, Dawn},
 booktitle = {2021 IEEE 37th International Conference on Data Engineering (ICDE)},
 year = {2021},
 pages = {193-204},
 doi = {10.1109/ICDE51399.2021.00024},
 url = {https://doi.ieeecomputersociety.org/10.1109/ICDE51399.2021.00024},
}
```

## How to install

```bash
apt-get install graphviz  # for ubuntu, similar command for other platform
pip3 install -e .
python3 -m spacy download en_core_web_sm
```

## How to use

```bash
st2g -i <input_file_path> -o <output_file_path>
```

or if you're using the source code:

```bash
python3 src/st2g/main.py -i <input_file_path> -o <output_file_path>
```

### Example

Input:

```txt
First, /usr/bin/wget will be started by /bin/bash . It downloads some data from 162.125.6.6, then writes the data to sysrep_exp_data.txt.
```

Output:

```txt
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
