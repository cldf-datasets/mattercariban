from pathlib import Path
import cldfbench
import pylexibank
import pycldf
from pycldf.sources import Sources, Reference

# Customize your basic data.
# if you need to store other data in columns than the lexibank defaults, then over-ride
# the table type (pylexibank.[Language|Lexeme|Concept|Cognate|]) and add the required columns e.g.
#
#import attr
#
#@attr.s
#class Concept(pylexibank.Concept):
#    MyAttribute1 = attr.ib(default=None)


class Dataset(pylexibank.Dataset):
    dir = Path(__file__).parent
    id = "mattercariban"

    # register custom data types here (or language_class, lexeme_class, cognate_class):
    #concept_class = Concept

    # define the way in which forms should be handled
    form_spec = pylexibank.FormSpec(
        brackets={"(": ")"},  # characters that function as brackets
        separators=";/,",  # characters that split forms e.g. "a, b".
        missing_data=('?', '-'),  # characters that denote missing data.
        strip_inside_brackets=True   # do you want data removed in brackets or not?
    )

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

    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.
        to download a temporary TSV file and convert to persistent CSV:

        >>> with self.raw_dir.temp_download("http://www.example.com/e.tsv", "example.tsv") as data:
        ...     self.raw_dir.write_csv('template.csv', self.raw_dir.read_csv(data, delimiter='\t'))
        """

    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.
        """
        with self.cldf_writer(args) as writer:
            writer.add_sources(*self.raw_dir.read_bib('cariban_resolved.bib'))
            cmap = writer.add_concepts(lookup_factory=lambda c: c.english)
            cmap['you'] = cmap['thou']
            cmap['grease/fat'] = cmap['grease']
            cmap['breast'] = cmap['breasts']
            cmap['son'] = cmap['person']
            data = pycldf.Dataset.from_metadata(self.raw_dir / 'cariban_data.json')
            for lang in data['LanguageTable']:
                writer.add_language(ID=lang['ID'], Name=lang['Name'])
            for lex in self.raw_dir.read_csv('cariban_swadesh_list.csv', dicts=True):
                #"Language_ID","Swadesh_Nr","Feature_ID","Value","Cognateset_ID","Source","Comment","Full_Form"
                for form in writer.add_lexemes(
                    Value=lex['Value'],
                    Parameter_ID=cmap[lex['Feature_ID']],
                    Language_ID=lex['Language_ID'],
                    Source=[Reference(*d) for d in [Sources.parse(lex['Source'].replace(';', ','))]]
                    if lex['Source'] and not lex['Source'].startswith('pc') else [],
                ):
                    writer.add_cognate(
                        lexeme=form,
                        Cognateset_ID='{}-{}'.format(cmap[lex['Feature_ID']], lex['Cognateset_ID']))

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
