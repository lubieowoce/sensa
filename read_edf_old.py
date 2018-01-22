# -*- coding: utf-8 -*-
# This module was created by Wiktor Rorot <wiktor.rorot@gmail.com> as a part of pytnam project
# (https://github.com/pytnam/pytnam) and is licensed under GNU GPL.

from collections import defaultdict
from io import FileIO
import numpy as np


def read_edf(path):

    """
    The function edf_reader serves to read .edf files.

    :argument path: string, a path to the .edf file

    :returns
        :return header: defaultdict(lambda: None), a dictionary containing general information about the recording,
            from the .edf file's header.
            It conveys following information:
                version (string): version of the .edf data format (always 0)
                patient_id (string): local patient id
                rec_id (string): local recording id
                stardate (string): startdate of the recording (dd.mm.yy) (for more info see EDF and EDF+ specs at:
                    http://www.edfplus.info/specs/index.html)
                starttime (string): starttime of the recording (hh.mm.ss)
                header_bytes (integer): size of the header (in bytes)
                reserved_general (string): reserved field of 44 characters; 
                    since introduction of EDF+ it conveys the information about the continuity of the record 
                    (see EDF+ specs)
                num_records (integer): the recording in the edf format is broken into records of not less than 1 second 
                    and no more than 61440 bytes (see specs);
                record_duration (float): duration of one record; usually an integer >= 1;
                ns (integer): number of signals in the recording (e.g. in EEG - number of channels)
                labels (list of strings): labels of signals;
                transducer (dictionary - string: string): key: label (an element of labels), value: transducer type;
                physical_dim (dictionary - string: string): key: label (an element of labels), value: physical dimension;
                physical_min (dictionary - string: float): key: label (an element of labels), value: physical minimum;
                physical_max (dictionary - string: float): key: label (an element of labels), value: physical maximum;
                digital_min (dictionary - string: float): key: label (an element of labels), value: digital minimum;
                digital_max (dictionary - string: float): key: label (an element of labels), value: digital maximum;
                prefiltering (dictionary - string: string): key: label (an element of labels), value: signal's prefiltering;
                num_samples (dictionary - string: integer): key: label (an element of labels), value: number of samples
                    in each record of the signal;
                reserved_signal (dictionary - string: string): key: label (an element of labels), value: a reserved
                    field of 32 characters;
                frequency (dictionary - string: float): key: label (an element of labels), value: frequency of the signal;

        :return signal: defaultdict(np.array) -- a dictionary of the following format: key: label, value: list of samples;

            NOTE: this version ignores the differences between edf and edf+, what makes her more suitable for edf,
            rather than edf+ files

            TODO: signal is represented in the digital or physical form? does it have to be transformed?
    """

    def read_header(data_file: FileIO):
        """Reads EDF file header."""

        def read_n_bytes(df: FileIO, n, method):
            return method(df.read(n).strip().decode('ascii'))

        def static_header(df: FileIO, hdr):

            header_keys_static = [('version', 8, str), ('patient_id', 80, str), ('rec_id', 80, str),
                                  ('startdate', 8, str),
                                  ('starttime', 8, str), ('header_bytes', 8, int), ('reserved_general', 44, str),
                                  ('num_records', 8, int), ('record_duration', 8, float), ('ns', 4, int)]
            # this part of code reads the part of the header with the general information about the record
            for key, n, method in header_keys_static:
                hdr[key] = read_n_bytes(df, n, method)
            return hdr

        def dynamic_header(df: FileIO, hdr):

            # this part reads the part of the header with the information about each signal
            ns = hdr['ns']

            hdr['labels'] = []
            for i in range(ns):
                hdr['labels'].append(df.read(16).strip().decode('ascii'))

            header_keys_dynamic = [('transducer', 80, str), ('physical_dim', 8, str), ('physical_min', 8, float),
                                   ('physical_max', 8, float), ('digital_min', 8, float), ('digital_max', 8, float),
                                   ('prefiltering', 80, str), ('num_samples', 8, int), ('reserved_signal', 32, str)]

            for key, n, method in header_keys_dynamic:
                hdr[key] = defaultdict(method)
                for label in hdr['labels']:
                    hdr[key][label] = read_n_bytes(df, n, method)

            return hdr

        header = dynamic_header(data_file, static_header(data_file, defaultdict(lambda: None)))
        # header = static_header(data_file, header)
        # header = dynamic_header(data_file, header)

        return header

    def read_signal(data_file: FileIO, header):
        """Reads EEG signal from the EDF file."""

        signal = {}
        num_records = header['num_records']
        rest = bytes(data_file.read())
        offset = 0
        dt = np.dtype(np.int16)
        dt = dt.newbyteorder('<')

        for label in header['labels']:
            num_samples = header['num_samples'][label]
            signal[label] = np.zeros(num_records * num_samples).reshape(num_records, num_samples)

        for i in range(num_records):
            for label in header['labels']:
                num_samples = header['num_samples'][label]
                signal[label][i] = np.frombuffer(rest, dtype=dt, count=num_samples, offset=offset)
                offset += num_samples * 2

        for label in header['labels']:
            num_samples = header['num_samples'][label]
            signal[label] = scale(header['physical_max'][label], header['digital_max'][label],
                                  np.array(signal[label].reshape(num_samples * num_records)))

        return signal

    # note: this function will increase the computational complexity of Reader
    def scale(physical_max, digital_max, signal):
        """Scales the signal from digital (arbitrary) to physical (uV) units."""
        signal *= physical_max / digital_max
        return signal

    data_file = open(path, 'rb')
    header = read_header(data_file)
    header['frequency'] = defaultdict(float)
    for label in header['labels']:
        header['frequency'][label] = header['num_samples'][label]/header['record_duration']
    signal = read_signal(data_file, header)
    data_file.close()
    return header, signal




