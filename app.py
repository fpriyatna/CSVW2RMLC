from flask import Flask, render_template, request
import csvw
import logging
import json

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
        #tg = csvw.TableGroup.from_file(csvw_url)
        #logging.info('tg : %s', tg)
        json_data = json.loads(open(csvw_url).read())
        logging.info('json_data = \n%s', json_data)
        logical_source = generate_logical_source(json_data)
        table_schema = json_data['tableSchema']
        columns = table_schema['columns']
        predicate_object_maps = generate_predicate_object_maps(columns)
        rmlc = '<TriplesMap>\n'
        rmlc = rmlc + logical_source + '\n'
        rmlc = rmlc + predicate_object_maps + '\n'
        rmlc = rmlc + '.\n'
        logging.info('rmlc = \n%s', rmlc)
        return rmlc


def generate_logical_source(json_data):
    url = json_data['url']
    logging.info('url = %s', url)
    logical_source = '\trml:logicalSource[\n'
    logical_source = logical_source + '\t\trml:source'
    logical_source = logical_source + ' "' + json_data['url'] + '";\n'
    logical_source = logical_source + '\t];\n'
    logging.info('logical_source = %s', logical_source)
    return logical_source


def generate_predicate_object_maps(columns):
    predicate_object_maps = ''
    for column in columns:
        predicate_object_map = '\trr:predicateObjectMap [\n'
        property_url = str(column['propertyUrl'])
        predicate_object_map = predicate_object_map + '\t\trr:predicate ' + property_url + ';\n'
        predicate_object_map = predicate_object_map + '\t\trr:objectMap [\n'
        column_name = column['name']
        predicate_object_map = predicate_object_map + '\t\t\t rr:reference "' + column_name + '";\n'
        predicate_object_map = predicate_object_map + '\t\t];\n\n'
        predicate_object_maps = predicate_object_maps + predicate_object_map
    return predicate_object_maps


if __name__ == '__main__':
    app.run(debug=True)
