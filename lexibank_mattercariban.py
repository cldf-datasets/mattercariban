from pathlib import Path
import cldfbench
import pylexibank
import pycldf
from pycldf.sources import Sources, Reference


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "mattercariban"
    writer_options = dict(keep_languages=False, keep_parameters=False)

    def cldf_specs(self):
        return {
            None: pylexibank.Dataset.cldf_specs(self),
            'structure': cldfbench.CLDFSpec(
                dir=self.cldf_dir,
                module='StructureDataset',
                data_fnames={'ParameterTable': 'features.csv'},
                writer_cls=cldfbench.CLDFWriter,
            ),
        }


    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.
        """
        with self.cldf_writer(args) as writer:
            writer.cldf.add_component('CognatesetTable')
            writer.add_sources(*self.raw_dir.read_bib('cariban_resolved.bib'))
            cmap = writer.add_concepts(lookup_factory=lambda c: c.english)
            data = pycldf.Dataset.from_metadata(self.raw_dir / 'cariban_data.json')
            for lang in data['LanguageTable']:
                writer.add_language(ID=lang['ID'], Name=lang['Name'], Glottocode=lang["Glottocode"])

            cs_seen = set()
            reconstructions = {
                tuple(c['ID'].split('-')): c['Form'] for c in
                self.raw_dir.read_csv('cariban_lexical_reconstructions.csv', dicts=True)}
            for lex in self.raw_dir.read_csv('cariban_swadesh_list.csv', dicts=True):
                #"Language_ID","Swadesh_Nr","Feature_ID","Value","Cognateset_ID","Source","Comment","Full_Form"
                if lex['Feature_ID'] not in cmap:
                    print(lex['Feature_ID'])
                    continue
                for form in writer.add_lexemes(
                    Value=lex['Value'],
                    Parameter_ID=cmap[lex['Feature_ID']],
                    Language_ID=lex['Language_ID'],
                    Source=[Reference(*d) for d in [Sources.parse(lex['Source'].replace(';', ','))]]
                    if lex['Source'] and not lex['Source'].startswith('pc') else [],
                ):
                    cs_key = (lex['Feature_ID'], lex['Cognateset_ID'])
                    cs_id = '{}-{}'.format(cmap[cs_key[0]], cs_key[1])
                    if cs_key not in cs_seen:
                        writer.objects['CognatesetTable'].append(dict(
                            ID=cs_id,
                            Description=reconstructions.get(cs_key),
                        ))
                        cs_seen.add(cs_key)
                    writer.add_cognate(lexeme=form, Cognateset_ID=cs_id)

            # Note: We want to re-use LanguageTable across the two CLDF datasets:
            LanguageTable = writer.cldf['LanguageTable']

        with self.cldf_writer(args, cldf_spec='structure', clean=False) as writer:
            writer.cldf.add_component(LanguageTable)  # we reuse the one from above!
            #writer.objects['ParameterTable'].append({'ID': 'f1'})
            #writer.objects['ValueTable'].append({
            #    'ID': 1,
            #    'Value': 'x',
            #    'Language_ID': 'abc',
            #    'Parameter_ID': 'f1',
            #})
