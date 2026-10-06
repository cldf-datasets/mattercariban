from pathlib import Path
import cldfbench
import pycldf
from pycldf.sources import Sources, Reference
from pylexibank import Dataset as BaseDataset
from pylexibank import FormSpec


def add_c_id(c_set, dic, counter=1):
    """Cognate ID counter"""
    if c_set not in dic:
        dic[c_set] = counter
        counter += 1
    return dic[c_set]


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "mattercariban"

    writer_options = {"keep_languages": False, "keep_parameters": False}

    # define the way in which forms should be handled
    form_spec = FormSpec(
        brackets={"(": ")"},
        separators=";/,",
        missing_data=('?', '-'),
        strip_inside_brackets=True,
        replacements=[("-", "")]
    )


    def cmd_makecldf(self, args):
        """
        Convert the raw data to a CLDF dataset.
        """
        args.writer.add_sources(*self.raw_dir.read_bib('cariban_resolved.bib'))
        args.log.info("added sources")

        cmap = args.writer.add_concepts(lookup_factory=lambda c: c.english)
        cmap['you'] = cmap['thou']
        cmap['grease/fat'] = cmap['grease']
        cmap['breast'] = cmap['breasts']
        cmap['son'] = cmap['person']
        # cmap['jaguar'] = cmap['']
        data = pycldf.Dataset.from_metadata(self.raw_dir / 'cariban_data.json')
        for lang in data['LanguageTable']:
            args.writer.add_language(ID=lang['ID'], Name=lang['Name'], Glottocode=lang["Glottocode"])

        # cs_seen = set()
        reconstructions = {
            c['ID']: (i, c['Form'])
            for i, c in enumerate(
                c for c in self.raw_dir.read_csv('cariban_lexical_reconstructions.csv', dicts=True)
                if c["Language_ID"] == 'cari1283'
            )
        }

        c_dic = {}
        for lex in self.raw_dir.read_csv('cariban_swadesh_list.csv', dicts=True):
            #"Language_ID","Swadesh_Nr","Feature_ID","Value","Cognateset_ID","Source","Comment","Full_Form"
            # Check for missing concepts
            if lex['Feature_ID'] not in cmap:
                print("Missing concept:", lex['Feature_ID'])
                continue

            # Add cognate set
            c_id = lex['Feature_ID'] + '-' + lex['Cognateset_ID']

            # Add lexemes
            lexeme = args.writer.add_lexemes(
                Value=lex['Value'],
                Parameter_ID=cmap[lex['Feature_ID']],
                Language_ID=lex['Language_ID'],
                Cognacy=add_c_id(c_id, c_dic),
                Source=[Reference(*d) for d in [Sources.parse(lex['Source'].replace(';', ','))]]
                if lex['Source'] and not lex['Source'].startswith('pc') else [],
            )

            # args.writer.add_cognate(
            #     lexeme=lexeme,
            #     Cognateset_ID=add_c_id(c_id, c_dic)#,
            #     Alignment=alignment,
            #     Alignment_Method="false",
            #     Alignment_Source="expert"
            #     )

        for rec in reconstructions:
            param = rec.split('-')[0]
            if param in cmap:
                args.writer.add_lexemes(
                    Value=rec[1],
                    Parameter_ID=cmap[param],
                    Language_ID='pc',
                    Cognacy=add_c_id(rec, c_dic),
                    Source="matter_cariban_phylo"
                )
