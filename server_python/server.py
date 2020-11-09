# Serve libgen-text files from /text, static search site from /text/search-site
# Access in any browser
import os, subprocess
from flask import Flask, Response, abort, redirect, send_from_directory
from werkzeug.routing import BaseConverter
app = Flask(__name__)

static_base = "/text/search-site"
book_base = "/text/text"

class Md5Converter(BaseConverter):
    regex = "[0-9a-fA-F]{32}"
    def to_python(self, value):
        return value.lower()
    def to_url(self, value):
        return value
class GroupConverter(BaseConverter):
    regex = "0|[1-9][0-9]*000"
    def to_python(self, value):
        return value
    def to_url(self, value):
        return value
app.url_map.converters['md5'] = Md5Converter
app.url_map.converters['group'] = GroupConverter

@app.route('/')
def index():
    return redirect('html/index-local.html')

@app.route('/<any(css,js,html):directory>/<filename>')
def static_file(directory, filename):
    return send_from_directory(os.path.join(static_base, directory), filename)

def xz_send(archive, member):
    try:
        text = subprocess.check_output(['tar', 'xOf', os.path.join(book_base, archive), member])
        return Response(text, mimetype='text/plain')
    except:
        abort(404, description="That file is not available in text format")

@app.route('/book/ff/<group:group>/<md5:md5>.txt')
def book_ff(group, md5):
    return xz_send("ff/" + group + ".tar.xz", group + "/" + md5+".txt")

@app.route('/book/lg/<group:group>/<md5:md5>.<extension>.txt')
def book_lg(group, md5, extension):
    return xz_send("lg/" + group + ".tar.xz", group + "/" + md5+"."+extension+".txt")

if __name__ == "__main__":
    app.run(debug=True)
