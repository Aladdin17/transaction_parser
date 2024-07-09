"""
File: parser.py
Author: Christien Alden
Purpose: Parses transactions and exports them to a various formats.
"""
from common.log import Log
import argparse
import os
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = 'Extract transactions from PDF to CSV.'
    )

    parser.add_argument('file', type = str, help = 'Statement to extract transactions from.')
    parser.add_argument('--importer', type = str, default = 'bankwest-pdf-1', required = False, help = 'Importer to use.')
    parser.add_argument('--exporter', type = str, default = 'csv', required = False, help = 'Exporter to use.')
    parser.add_argument('-o', dest = 'output', type = str, required = False, help = 'Output file.')
    parser.add_argument('-q', dest = 'quiet', action = 'store_true', help = 'Suppress all output.')

    # parse arguments setup program
    args = parser.parse_args()
    file_path : str = os.path.relpath(args.file)
    log = Log(quiet = args.quiet, fill_width = 60, fill_char = '.')

    # select importer
    if args.importer == 'bankwest-pdf-1':
        from importers.bankwest_pdf_1 import BankwestPDF1
        importer = BankwestPDF1(logger = Log(log.quiet, log.indent_level + 1, log.fill_width, log.fill_char))
    else:
        log(f'Importer {args.importer} not found.', file = sys.stderr)
        sys.exit(1)

    # select exporter
    if args.exporter == 'csv':
        from exporters.csv import CSV
        exporter = CSV(logger = Log(log.quiet, log.indent_level + 1, log.fill_width, log.fill_char))
    elif args.exporter == 'json':
        from exporters.json import JSON
        exporter = JSON(logger = Log(log.quiet, log.indent_level + 1, log.fill_width, log.fill_char))
    else:
        log(f'Exporter {args.exporter} not found.', file = sys.stderr)
        sys.exit(1)

    # extract transactions from file
    try:
        log(f'Importing transactions from \'{file_path}\' using \'{args.importer}\'')
        transactions = importer.extract(file_path)
        log('\n')
    except Exception as error:
        sys.exit(1)

    # convert transactions to exported format
    try:
        log(f'Converting transactions using \'{args.exporter}\'')
        exported_contents = exporter.export(transactions)
        log('\n')
    except Exception as e:
        sys.exit(1)

    # write exported contents to stdout if no output file is specified
    if not args.output:
        log.action('Writing transactions to \'stdout\'', 5)
        log('\n')
        print(exported_contents)
        sys.exit(0)

    # write exported contents to output file
    try:
        log.action(f'Writing transactions to \'{args.output}\'', 5)
        with open(args.output, 'w', newline = '') as stream:
            stream.write(exported_contents)
            log.success()
    except Exception as error:
        log.error(error)
        sys.exit(1)
