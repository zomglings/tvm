#!/usr/bin/env python

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""
TVMC - TVM driver command-line interface
"""
import argparse
from distutils.util import strtobool
import logging
import sys
import textwrap

import tvm
from humbug.report import Report

from tvm.driver.tvmc.common import TVMCException
from tvm.reporter import tvm_reporter, save_reporting_config


REGISTERED_PARSER = []


def register_parser(make_subparser):
    """
    Utility function to register a subparser for tvmc.

    Functions decorated with `tvm.driver.tvmc.main.register_parser` will be invoked
    with a parameter containing the subparser instance they need to add itself to,
    as a parser.

    Example
    -------

        @register_parser
        def _example_parser(main_subparser):
            subparser = main_subparser.add_parser('example', help='...')
            ...

    """
    REGISTERED_PARSER.append(make_subparser)
    return make_subparser


def _main(argv):
    """ TVM command line interface. """

    parser = argparse.ArgumentParser(
        prog="tvmc",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="TVM compiler driver",
        epilog=__doc__,
    )
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase verbosity")
    parser.add_argument("--version", action="store_true", help="print the version and exit")
    parser.add_argument(
        "--reporting",
        choices=["True", "False"],
        help="enable or disable sending crash reports to TVM",
    )

    subparser = parser.add_subparsers(title="commands")
    for make_subparser in REGISTERED_PARSER:
        make_subparser(subparser)

    args = parser.parse_args(argv)
    if args.verbose > 4:
        args.verbose = 4

    logging.getLogger("TVMC").setLevel(40 - args.verbose * 10)

    if args.version:
        sys.stdout.write("%s\n" % tvm.__version__)
        return 0

    if args.reporting:
        reporting_notice = textwrap.dedent(
            """
            Privacy policy:
            We collect basic system information and crash reports so that we can keep
            improving your experience using TVM to work with your data.
            You can find out more by reading our privacy policy:
                https://octoml.ai
            If you would like to opt out of reporting crashes and system information,
            run the following command:
                $ tvmc --reporting False
            """
        )

        reporting_choice = bool(strtobool(args.reporting))
        report = Report(
            title="Consent change",
            tags=tvm_reporter.system_tags(),
            content="Consent? `{}`".format(reporting_choice),
        )
        tvm_reporter.publish(report)
        save_reporting_config(reporting_choice)

        sys.stdout.write("%s\n" % reporting_notice)
        return 0

    if not hasattr(args, "func"):
        # In case no valid subcommand is provided, show usage and exit
        parser.print_help(sys.stderr)
        return 1

    try:
        return args.func(args)
    except TVMCException as err:
        sys.stderr.write("Error: %s\n" % err)
        return 4


def main():
    sys.exit(_main(sys.argv[1:]))


if __name__ == "__main__":
    main()
