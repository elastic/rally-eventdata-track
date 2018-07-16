#!/usr/bin/env python3
"""Validator for challenges

Simple script to validate jinja2 enriched challenges are valid json.
"""

import argparse
import glob
import json
import os
import jinja2

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "fileglob", type=str,
        help="File or glob pattern to match files")

    args = parser.parse_args()
    if args.fileglob:
        return glob.iglob(args.fileglob)

def validate_templates(files):
    error_found = None
    for file_tmpl in files:
        abs_dirname = os.path.join(os.getcwd(), os.path.dirname(file_tmpl))
        filename = os.path.basename(file_tmpl)
        print(">>> Parsing file: {}".format(os.path.join(abs_dirname, filename)))
        templateLoader = jinja2.FileSystemLoader(searchpath=abs_dirname)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(filename)
        try:
            json_output = json.loads(template.render())
        except json.JSONDecodeError:
            rendered_filename = "rendered"+filename
            print("Couldn't decode <{}> in json.".format(file_tmpl))
            print("Saving the rendered json template as <{}> so that you can inspect it in an editor".format("rendered"+rendered_filename))
            with open(rendered_filename, 'wt') as fp:
                fp.write(template.render())
            error_found = True

    if not error_found:
        print("Congratulations, no errors found.")

if __name__ == '__main__':
    files_to_parse = parse_args()
    validate_templates(files_to_parse)
