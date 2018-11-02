from flask import Flask, render_template, request
import csvw
import logging


app = Flask(__name__)
logging.basicConfig(filename='csvw2rmlc.log', level=logging.DEBUG)


@app.route('/')
def transformer():
    return render_template('transformer.html')


@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        result = request.form
        csvw_url = request.form['csvw_url']
        tg = csvw.TableGroup.from_file(csvw_url)
        logging.warning('tg = %s', tg)
        rmlc_url = transform_csvw_to_rmlc(csvw_url)
        return render_template("result.html", result=result, rmlc_url=rmlc_url)


def transform_csvw_to_rmlc(csvw_url):
        rmlc_url = csvw_url
        return rmlc_url


if __name__ == '__main__':
    app.run(debug=True)
