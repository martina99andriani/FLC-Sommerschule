#From the XML output from CTE:
#- May need to add one or more <div> elements between the text/body element and the <p> elements. The XSL script expects 2 divs between these two.
#- Run /home/matt/docx_tei_cte_conversion/extract_text_collate.xsl on the file. Save the result to /home/matt/results/collation/marculf/txt_from_XML. The file name should end with '_input.txt'

#Then run the following in Python:

from glob import glob
import os
import json
from string import punctuation
import re
import argparse

# to rstrip any punctuation that is not a closing square bracket
punct = punctuation.replace(']', '')

# This is the function to produce the lines in the CSV file 
def make_lines(json):
    lines = []
    temp_lines = []
    for i, w in enumerate(json['witnesses']):
        line = [x[i][0]['t'] if x[i] else '-' for x in json['table']]
        temp_lines.append(['{}\t{}'.format(w, '\t'.join(line[x:x+500])) for x in range(0, len(line), 500)])
    for i, l in enumerate(temp_lines[0]):
        lines.append(l)
        for other_l in temp_lines[1:]:
            lines.append(other_l[i])
        lines.append('\n')
    return lines
    
def make_lower(word):
    if word.isupper():
        return word
    else:
        return word.lower()

def collate_to_csv(formula, work_folder, baseline_sigla, collatex_location, special=''):
    # create collatex json input file 
    txt_inputs = glob(os.path.join(work_folder, 'txt_from_XML', special, '{}_*_input.txt'.format(formula)))
    print(txt_inputs)
    json_input_filename = os.path.join(work_folder, 'collatex_json_input', '{}{}_input.json'.format(formula, '_' + special if special else ''))

    wits = []
    for i in sorted(txt_inputs):
        wit_id = os.path.basename(i).split('_')[2]
        with open(i) as f:
            txt = f.read().split('******\n')[3]
        wits.append({'id': wit_id, 'tokens': [{'t': make_lower(w.rstrip(punct))} for w in txt.split() if w.rstrip(punct)]})
        if baseline_sigla in i:
            base_text = [{'t': w} for w in txt.split()]

    with open(json_input_filename, mode="w") as f:
        json.dump({'witnesses': wits}, f)

    # Run collatex on json input file 
    json_output_filename = os.path.join(work_folder, 'collatex_output', os.path.basename(json_input_filename).replace('_input', '_output'))
    os.system('~/java/11.0.17-ms/bin/java -jar {collatex} -f json -t -o {output} {input}'.format(collatex=collatex_location, output=json_output_filename, input=json_input_filename))

    # Produce the CSV file with the results 
    csv_output_filename = json_output_filename.replace('.json', '.csv')
    with open(json_output_filename) as f:
        r = json.load(f)
    with open(csv_output_filename, mode="w") as f:
        f.write('\n'.join(make_lines(r)))
    return base_text, json_output_filename

    
def produce_cte_xml(base_text, json_output_filename, script_dir, baseline_sigla):
    # Produce the XML input files for CTE 
    with open(json_output_filename) as f:                  
        output = json.load(f)

    with open(os.path.join(script_dir, 'CTE_XML_stub.xml')) as f:
        xml_output = f.read()

    note_num = 1

    # for many witnesses
    witnesses = sorted(output['witnesses'])
    baseline_index = witnesses.index(baseline_sigla)
    witnesses.pop(baseline_index)
    # Add placeholders for missing words in the base_text list
    for i, v in enumerate(output['table']):
        if v[baseline_index] == []:
            base_text.insert(i, [])

    for base_i, token_deep in enumerate(output['table']):
        token = [x[0]['t'] if x else ' ' for x in token_deep]
        baseline = token.pop(baseline_index)
        output_text = base_text[base_i]['t'].replace('<', '&lt;').replace('>', '&gt;') if baseline != ' ' else '<hi rend="font-style:italic; font-weight: bold;">fehlt</hi>'
        token_set = list(set(token))
        d = {}
        readings = []
        beg_note = ' <note type="a1" place="foot" xml:id="ftn{num}" n="{num}"><p>'.format(num=note_num)
        end_note = '</p></note>'
        for t in token_set:
            i = 0
            while t in token[i:]:
                new_index = token.index(t, i)
                try:
                    if new_index not in d[t]:
                        d[t].append(token.index(t, i))
                except KeyError:
                    d[t] = [token.index(t, i)]
                i += 1
        for k in sorted(d.keys(), key=lambda x: d[x]):
            if k != baseline:
                readings.append('{reading} {witness}'.format(witness=', '.join(['<hi rend="font-size:10pt;font-style:italic;">{}</hi><hi rend="font-size:10pt;font-style:italic;vertical-align:sub;font-size:smaller;">{}</hi>'.format(re.search(r'(\D+)(\d*[a-z]?)', witnesses[x]).groups('')[0], re.search(r'(\D+)(\d*[a-z]?)', witnesses[x]).groups('')[1].lstrip('0')) for x in d[k]]), reading=k.replace('<', '&lt;').replace('>', '&gt;') if k != ' ' else '<hi rend="font-style:italic;">fehlt</hi>'))
        if readings:
            output_text += beg_note + '; '.join(readings) + end_note
            note_num += 1
        xml_output += output_text + ' '
        
    xml_output += '</p></div></body></text></TEI>'

    with open(json_output_filename.replace('.json', '_finished.xml'), mode="w") as f:
        f.write(xml_output)
        
def run_process(formula, baseline, folder, collatex, script_dir, with_special=True):
    base_text, json_output_filename = collate_to_csv(formula=formula, work_folder=folder, special='', baseline_sigla=baseline, collatex_location=collatex)
    produce_cte_xml(base_text=base_text, json_output_filename=json_output_filename, script_dir=script_dir, baseline_sigla=baseline)
    if with_special:
        collate_to_csv(formula=formula, work_folder=folder, special='special', baseline_sigla=baseline, collatex_location=collatex)
        
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(prog="collate_CTE_collatex_CTE.py")
    parser.add_argument('--prefix', help="The filename prefix for the .txt input files. For example, to collate the files 'marculf_2_P12_input.txt' and 'marculf_2_P16_input.txt' together, the prefix would be 'marculf_2'.")
    parser.add_argument('--baseline', help="The siglum of the manuscript to use as the baseline text for the resulting CTE XML file.")
    parser.add_argument('--folder', help="The folder that contains the 'txt_from_XML', the 'collatex_json_input' and the 'collatex_output' folders.")
    parser.add_argument('--collatex', help="The complete path to your collatex .jar file")
    parser.add_argument('--special', help="Add the --special flag if you have special manuscript collations in the 'txt_from_XML/special' folder that should be collated together separately. This will produce a separate .csv file that contains only these special manuscripts.", action="store_true")
    input_args = vars(parser.parse_args())
    run_process(formula=input_args['prefix'], baseline=input_args['baseline'], folder=input_args['folder'], collatex=input_args['collatex'], with_special=input_args['special'], script_dir=script_dir)
    
    
