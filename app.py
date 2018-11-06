from flask import Flask, render_template, request
import csvw
import logging
import json
import re
import urlparse, os

app = Flask(__name__)
logging.basicConfig(filename='csvw2rmlc.log', level=logging.DEBUG)


@app.route('/')
def transformer():
    return render_template('transformer.html')


@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        csvw_url = request.form['csvw_url']
        rmlc = transform_csvw_to_rmlc(csvw_url)
        return render_template("result.html", form_inputs=request.form, rmlc=rmlc)


def transform_csvw_to_rmlc(csvw_url):
    # tg = csvw.TableGroup.from_file(csvw_url)
    # logging.info('tg : %s', tg)
    json_data = json.loads(open(csvw_url).read())
    # logging.info('json_data = \n%s', json_data)
    rmlc = ''
    rmlc = rmlc + '@prefix rr: <http://www.w3.org/ns/r2rml#>.' + '\n'
    rmlc = rmlc + '@prefix rml: <http://semweb.mmlab.be/ns/rml#> .' + '\n'
    rmlc = rmlc + '@prefix rmlc: <http://www.oeg-upm.net/ns/rmlc#> .' + '\n'
    rmlc = rmlc + '@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.' + '\n'
    rmlc = rmlc + '@prefix ex: <http://www.example.com/> .' + '\n'
    rmlc = rmlc + '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .' + '\n'
    rmlc = rmlc + '@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.' + '\n'
    rmlc = rmlc + '@prefix schema: <http://schema.org/>.' + '\n'
    rmlc = rmlc + '\n'

    if 'tables' in json_data:
        for table in json_data['tables']:
            triples_map = generate_triples_map(table)
            rmlc = rmlc + triples_map + '\n'
    else:
        triples_map = generate_triples_map(json_data)
        rmlc = rmlc + triples_map + '\n'
        return rmlc

    logging.info('rmlc = \n%s', rmlc)
    print rmlc
    return rmlc


def get_filename_with_extension(url):
    parsed_url = urlparse.urlparse(url)
    filename_with_extension = os.path.basename(parsed_url.path)
    return filename_with_extension


def generate_triples_map(json_data):
    logical_source = generate_logical_source(json_data)
    table_schema = json_data['tableSchema']
    url = json_data['url']
    # filename, extension = url.split(".")
    filename_with_extension = get_filename_with_extension(url)
    filename, extension = filename_with_extension.split(".")
    triples_map = '<' + filename + '>\n'
    triples_map = triples_map + logical_source + '\n'
    if 'aboutUrl' in table_schema:
        about_url = table_schema['aboutUrl']
        subject_map = generate_subject_map(about_url)
        triples_map = triples_map + subject_map + '\n'
    columns = table_schema['columns']
    predicate_object_maps = generate_predicate_object_maps(columns)
    triples_map = triples_map + predicate_object_maps + '\n'
    if 'foreignKeys' in table_schema:
        ref_object_map = generate_ref_object_map(table_schema['foreignKeys'])
        triples_map = triples_map + ref_object_map + '\n'
    triples_map = triples_map + '.\n'
    # logging.info('triples_map = \n%s', triples_map)
    return triples_map


def generate_subject_map(about_url):
    about_url = re.sub('{#', '{', about_url)
    subject_map = ''
    subject_map = subject_map + '\trr:subjectMap [\n'
    subject_map = subject_map + '\t\trr:template "' + str(about_url) + '";\n'
    subject_map = subject_map + '\t];\n'
    return subject_map


def generate_logical_source(json_data):
    url = json_data['url']
    logging.info('url = %s', url)
    logical_source = '\trml:logicalSource [\n'
    logical_source = logical_source + '\t\trml:source'
    logical_source = logical_source + ' "' + json_data['url'] + '";\n'
    logical_source = logical_source + '\t];\n'
    #logging.info('logical_source = %s', logical_source)
    return logical_source


def generate_predicate_object_maps(columns):
    predicate_object_maps = ''
    for column in columns:
        if 'propertyUrl' in column:
            predicate_object_map = '\trr:predicateObjectMap [\n'
            predicate_map = generate_predicate_map(column)
            predicate_object_map = predicate_object_map + predicate_map
            object_map = generate_object_map(column)
            predicate_object_map = predicate_object_map + object_map
            predicate_object_map = predicate_object_map + '\t];\n'
            predicate_object_maps = predicate_object_maps + predicate_object_map
    return predicate_object_maps


def generate_predicate_map(column):
    predicate_map = ''
    property_url = str(column['propertyUrl'])
    property_url = re.sub('{#_', '{', property_url)
    predicate_map = predicate_map + '\t\trr:predicate ' + property_url + ';\n'
    return predicate_map


def generate_object_map(column):
    object_map = ''
    object_map = object_map + '\t\trr:objectMap [\n'
    if 'valueUrl' in column:
        value_url = column['valueUrl']
        object_map = object_map + '\t\t\t rr:template "' + value_url + '";\n'
    else:
        column_name = column['name']
        object_map = object_map + '\t\t\t rml:reference "' + column_name + '";\n'

    if 'datatype' in column:
        datatype = column['datatype']
        if 'base' in datatype:
            object_map = object_map + '\t\t\t rr:datatype "' + datatype['base'] + '";\n'
        else:
            object_map = object_map + '\t\t\t rr:datatype "' + column['datatype'] + '";\n'
    object_map = object_map + '\t\t];\n'
    return object_map


def generate_ref_object_map(foreign_keys):
    ref_object_map = ''
    ref_object_map = ref_object_map + '\trr:predicateObjectMap [\n'
    ref_object_map = ref_object_map + '\t\trr:predicate ex:hasSomething;\n'
    ref_object_map = ref_object_map + '\t\trr:objectMap [\n'
    for foreignKey in foreign_keys:
        column_reference = foreignKey['columnReference']
        logging.info('column_reference = %s', column_reference)
        reference = foreignKey['reference']
        reference_resource = reference['resource']
        logging.info('reference_resource = %s', reference_resource)
        reference_column_reference = reference['columnReference']
        logging.info('reference_column_reference = %s', reference_column_reference)
        # filename, extension = reference_resource.split(".")
        filename_with_extension = get_filename_with_extension(reference_resource)
        filename, extension = filename_with_extension.split(".")

        ref_object_map = ref_object_map + '\t\t\trr:parentTriplesMap <' + filename + '>;\n'
        ref_object_map = ref_object_map + '\t\t\trr:joinCondition [\n'
        ref_object_map = ref_object_map + '\t\t\t\trr:child "' + column_reference + '";\n'
        ref_object_map = ref_object_map + '\t\t\t\trr:parent "' + reference_column_reference + '";\n'
        ref_object_map = ref_object_map + '\t\t\t];\n'
    ref_object_map = ref_object_map + '\t\t];\n'
    ref_object_map = ref_object_map + '\t];\n'
    return ref_object_map

# def get_class():


if __name__ == '__main__':
    app.run(debug=True)
