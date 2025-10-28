# wfm2readframe.py
import os
import struct
import re
import warnings
import numpy as np


class WfmReadError(Exception):
    pass


def _read_struct(f, fmt):
    size = struct.calcsize(fmt)
    data = f.read(size)
    if len(data) != size:
        raise WfmReadError("Lectura incompleta: se esperaban {} bytes, leídos {}".format(size, len(data)))
    return struct.unpack(fmt, data)


def _read_fmt(f, endian, base_fmt, count=1):
    fmt = endian + base_fmt
    if count == 1:
        return _read_struct(f, fmt)[0]
    else:
        size = struct.calcsize(fmt) * count
        data = f.read(size)
        if len(data) != size:
            raise WfmReadError("Lectura incompleta (array).")
        return struct.unpack(fmt * count, data)


def _read_chars_until_null(bytes_block):
    # devuelve string hasta el primer \x00
    idx = bytes_block.find(b'\x00')
    if idx == -1:
        return bytes_block.decode(errors='ignore')
    else:
        return bytes_block[:idx].decode(errors='ignore')


def wfm2readframe(filename, frame, datapoints=None, step=1, startind=1):
    """
    Traducción fiel a Python del wfm2readframe.m de Erik Benkler.
    Devuelve: y, t, info, ind_over, ind_under
    """

    # --- comprobaciones iniciales de argumentos ---
    if step is None:
        step = 1
    if startind is None:
        startind = 1
    if datapoints is not None and (datapoints < 1 or int(datapoints) != datapoints):
        raise ValueError("datapoints debe ser entero positivo si se especifica.")

    # normalizar nombre fichero
    base_p, base_n = os.path.split(filename)
    if base_p == '':
        base_p = '.'
    name_noext, ext = os.path.splitext(base_n)
    if ext.lower() != '.wfm':
        filename = os.path.join(base_p, name_noext + '.wfm')
    else:
        filename = os.path.join(base_p, base_n)

    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Invalid file name: {filename}")

    info = {}

    with open(filename, 'rb') as f:
        # byte order verification (uint16)
        b = f.read(2)
        if len(b) < 2:
            raise WfmReadError("Archivo demasiado corto.")
        # leer como little endian primero para comparar con 0x0F0F
        v_le = struct.unpack('<H', b)[0]
        if v_le == 0x0F0F:
            endian = '<'  # little-endian
            info['byte_order_verification'] = format(v_le, '04X')
        else:
            # si no coincide, asumimos big-endian
            v_be = struct.unpack('>H', b)[0]
            endian = '>'
            info['byte_order_verification'] = format(v_be, '04X')

        # versioning_number: 8 bytes string
        ver_bytes = f.read(8)
        info['versioning_number'] = ver_bytes.decode(errors='ignore')
        # intentar parsear WFM#n
        m = re.search(r':?WFM#\s*?(\d{1,3})', info['versioning_number'])
        if m:
            wfm_version = int(m.group(1))
        else:
            # fallback: coger dígitos finales si existen
            digits = re.findall(r'\d+', info['versioning_number'])
            wfm_version = int(digits[-1]) if digits else 1
        if wfm_version > 3:
            warnings.warn("WFM2read:HigherVersionNumber - wfm2read has only been tested with WFM file versions <= 3")

        # ahora seguir lectura tal como en MATLAB: varios campos con el endianness detectado
        # num_digits_in_byte_count : uint8
        info['num_digits_in_byte_count'] = _read_fmt(f, endian, 'B')
        info['num_bytes_to_EOF'] = _read_fmt(f, endian, 'i')  # int32
        info['num_bytes_per_point'] = _read_fmt(f, endian, 'B')  # uint8
        info['byte_offset_to_beginning_of_curve_buffer'] = _read_fmt(f, endian, 'I')  # uint32
        info['horizontal_zoom_scale_factor'] = _read_fmt(f, endian, 'i')  # int32
        info['horizontal_zoom_position'] = _read_fmt(f, endian, 'f')  # float32
        info['vertical_zoom_scale_factor'] = _read_fmt(f, endian, 'd')  # double
        info['vertical_zoom_position'] = _read_fmt(f, endian, 'f')  # float32

        dummy = f.read(32)
        info['waveform_label'] = _read_chars_until_null(dummy)

        info['N'] = _read_fmt(f, endian, 'I')  # uint32
        info['size_of_waveform_header'] = _read_fmt(f, endian, 'H')  # uint16

        # --- waveform header ---
        # setType: 4 * int8
        info['setType'] = struct.unpack(endian + '4b', f.read(4))
        info['wfmCnt'] = _read_fmt(f, endian, 'I')
        f.read(24)  # skip bytes 86..109 (not used)
        info['wfm_update_spec_count'] = _read_fmt(f, endian, 'I')
        info['imp_dim_ref_count'] = _read_fmt(f, endian, 'I')
        info['exp_dim_ref_count'] = _read_fmt(f, endian, 'I')
        # data_type: 4 * int8
        info['data_type'] = struct.unpack(endian + '4b', f.read(4))
        f.read(16)  # skip bytes 126..141
        info['curve_ref_count'] = _read_fmt(f, endian, 'I')
        info['num_req_fast_frames'] = _read_fmt(f, endian, 'I')
        info['num_acq_fast_frames'] = _read_fmt(f, endian, 'I')

        if wfm_version >= 2:
            info['summary_frame_type'] = _read_fmt(f, endian, 'H')

        # pixmap stuff
        info['pixmap_display_format'] = struct.unpack(endian + '4b', f.read(4))
        # uint64 (cuidado con plataformas) -> leer como unsigned long long
        info['pixmap_max_value'] = _read_fmt(f, endian, 'Q')

        # --- explicit dimension 1 (ed1) ---
        ed1 = {}
        ed1['dim_scale'] = _read_fmt(f, endian, 'd')
        ed1['dim_offset'] = _read_fmt(f, endian, 'd')
        ed1['dim_size'] = _read_fmt(f, endian, 'I')
        dummy = f.read(20)
        ed1['units'] = _read_chars_until_null(dummy)
        ed1['dim_extent_min'] = _read_fmt(f, endian, 'd')
        ed1['dim_extent_max'] = _read_fmt(f, endian, 'd')
        ed1['dim_resolution'] = _read_fmt(f, endian, 'd')
        ed1['dim_ref_point'] = _read_fmt(f, endian, 'd')
        ed1['format'] = struct.unpack(endian + '4b', f.read(4))
        ed1['storage_type'] = struct.unpack(endian + '4b', f.read(4))
        ed1['n_value'] = _read_fmt(f, endian, 'i')
        ed1['over_range'] = _read_fmt(f, endian, 'i')
        ed1['under_range'] = _read_fmt(f, endian, 'i')
        ed1['high_range'] = _read_fmt(f, endian, 'i')
        ed1['low_range'] = _read_fmt(f, endian, 'i')
        ed1['user_scale'] = _read_fmt(f, endian, 'd')
        # user_units: 20 bytes then trim at NULL
        ed1['user_units'] = _read_chars_until_null(f.read(20))
        # user_offset variable name in MATLAB seems mal nombrado (ed1.user_offset)
        ed1['user_offset'] = _read_fmt(f, endian, 'd')

        if wfm_version >= 3:
            ed1['point_density'] = _read_fmt(f, endian, 'd')
        else:
            ed1['point_density'] = _read_fmt(f, endian, 'I')

        ed1['href'] = _read_fmt(f, endian, 'd')
        ed1['trig_delay'] = _read_fmt(f, endian, 'd')

        # --- explicit dimension 2 (ed2) ---
        ed2 = {}
        ed2['dim_scale'] = _read_fmt(f, endian, 'd')
        ed2['dim_offset'] = _read_fmt(f, endian, 'd')
        ed2['dim_size'] = _read_fmt(f, endian, 'I')
        dummy = f.read(20)
        ed2['units'] = _read_chars_until_null(dummy)
        ed2['dim_extent_min'] = _read_fmt(f, endian, 'd')
        ed2['dim_extent_max'] = _read_fmt(f, endian, 'd')
        ed2['dim_resolution'] = _read_fmt(f, endian, 'd')
        ed2['dim_ref_point'] = _read_fmt(f, endian, 'd')
        ed2['format'] = struct.unpack(endian + '4b', f.read(4))
        ed2['storage_type'] = struct.unpack(endian + '4b', f.read(4))
        ed2['n_value'] = _read_fmt(f, endian, 'i')
        ed2['over_range'] = _read_fmt(f, endian, 'i')
        ed2['under_range'] = _read_fmt(f, endian, 'i')
        ed2['high_range'] = _read_fmt(f, endian, 'i')
        ed2['low_range'] = _read_fmt(f, endian, 'i')
        ed2['user_scale'] = _read_fmt(f, endian, 'd')
        ed2['user_units'] = _read_chars_until_null(f.read(20))
        ed2['user_offset'] = _read_fmt(f, endian, 'd')
        if wfm_version >= 3:
            ed2['point_density'] = _read_fmt(f, endian, 'd')
        else:
            ed2['point_density'] = _read_fmt(f, endian, 'I')
        ed2['href'] = _read_fmt(f, endian, 'd')
        ed2['trig_delay'] = _read_fmt(f, endian, 'd')

        # --- implicit dimension 1 (id1) ---
        id1 = {}
        id1['dim_scale'] = _read_fmt(f, endian, 'd')
        id1['dim_offset'] = _read_fmt(f, endian, 'd')
        id1['dim_size'] = _read_fmt(f, endian, 'I')
        id1['user_units'] = _read_chars_until_null(f.read(20))
        # note: in MATLAB they call this info.id1.units earlier; preserve key naming
        id1['units'] = id1['user_units']
        id1['dim_extent_min'] = _read_fmt(f, endian, 'd')
        id1['dim_extent_max'] = _read_fmt(f, endian, 'd')
        id1['dim_resolution'] = _read_fmt(f, endian, 'd')
        id1['dim_ref_point'] = _read_fmt(f, endian, 'd')
        id1['spacing'] = _read_fmt(f, endian, 'I')
        id1['user_scale'] = _read_fmt(f, endian, 'd')
        id1['user_units'] = _read_chars_until_null(f.read(20))
        id1['user_offset'] = _read_fmt(f, endian, 'd')
        if wfm_version >= 3:
            id1['point_density'] = _read_fmt(f, endian, 'd')
        else:
            id1['point_density'] = _read_fmt(f, endian, 'I')
        id1['href'] = _read_fmt(f, endian, 'd')
        id1['trig_delay'] = _read_fmt(f, endian, 'd')

        # --- implicit dimension 2 (id2) ---
        id2 = {}
        id2['dim_scale'] = _read_fmt(f, endian, 'd')
        id2['dim_offset'] = _read_fmt(f, endian, 'd')
        id2['dim_size'] = _read_fmt(f, endian, 'I')
        id2['units'] = _read_chars_until_null(f.read(20))
        id2['dim_extent_min'] = _read_fmt(f, endian, 'd')
        id2['dim_extent_max'] = _read_fmt(f, endian, 'd')
        id2['dim_resolution'] = _read_fmt(f, endian, 'd')
        id2['dim_ref_point'] = _read_fmt(f, endian, 'd')
        id2['spacing'] = _read_fmt(f, endian, 'I')
        id2['user_scale'] = _read_fmt(f, endian, 'd')
        id2['user_units'] = _read_chars_until_null(f.read(20))
        id2['user_offset'] = _read_fmt(f, endian, 'd')
        if wfm_version >= 3:
            id2['point_density'] = _read_fmt(f, endian, 'd')
        else:
            id2['point_density'] = _read_fmt(f, endian, 'I')
        id2['href'] = _read_fmt(f, endian, 'd')
        id2['trig_delay'] = _read_fmt(f, endian, 'd')

        # time base 1
        info['tb1_real_point_spacing'] = _read_fmt(f, endian, 'I')
        info['tb1_sweep'] = struct.unpack(endian + '4b', f.read(4))
        info['tb1_type_of_base'] = struct.unpack(endian + '4b', f.read(4))

        # time base 2
        info['tb2_real_point_spacing'] = _read_fmt(f, endian, 'I')
        info['tb2_sweep'] = struct.unpack(endian + '4b', f.read(4))
        info['tb2_type_of_base'] = struct.unpack(endian + '4b', f.read(4))

        # --- comprobar existencia del frame pedido ---
        # MATLAB uses (~isa(frame,'integer') && ((frame>(info.N+1)) || (frame<=0))) - we check integer-ness
        if not (isinstance(frame, int)):
            raise ValueError("El parámetro frame debe ser un entero.")
        if (frame > (info['N'] + 1)) or (frame <= 0):
            raise ValueError(f"Frame number {frame} provided in call to wfm2readframe does not exist in file {filename}")

        # guardamos posición antes de la update spec (equivalente ftell)
        pos_before_updatespec = f.tell()  # en MATLAB comentan que vale 768 para wfm002

        # si frame>1, mover al bloque de actualización específico
        if frame > 1:
            # desplazamiento: pos_before_updatespec + 54 + (frame-2)*24
            f.seek(pos_before_updatespec + 54 + (frame - 2) * 24, os.SEEK_SET)

        # wfm update specification (para frame solicitado)
        info['real_point_offset'] = _read_fmt(f, endian, 'I')
        info['tt_offset'] = _read_fmt(f, endian, 'd')
        info['frac_sec'] = _read_fmt(f, endian, 'd')
        info['GMT_sec'] = _read_fmt(f, endian, 'i')

        if frame > 1:
            f.seek(pos_before_updatespec + 54 + info['N'] * 24 + (frame - 2) * 30, os.SEEK_SET)

        # wfm curve information
        info['state_flags'] = _read_fmt(f, endian, 'I')
        info['type_of_checksum'] = struct.unpack(endian + '4b', f.read(4))
        info['checksum'] = _read_fmt(f, endian, 'h')  # int16
        info['precharge_start_offset'] = _read_fmt(f, endian, 'I')
        info['data_start_offset'] = _read_fmt(f, endian, 'I')
        info['postcharge_start_offset'] = _read_fmt(f, endian, 'I')
        info['postcharge_stop_offset'] = _read_fmt(f, endian, 'I')
        info['end_of_curve_buffer_offset'] = _read_fmt(f, endian, 'I')

        # decidir formato de datos según ed1.format(1)
        fmt_code = ed1['format'][0]  # primer elemento
        # mapa de formatos basado en el .m
        if fmt_code == 0:
            np_fmt = 'i2'  # int16
        elif fmt_code == 1:
            np_fmt = 'i4'  # int32
        elif fmt_code == 2:
            np_fmt = 'u4'  # uint32
        elif fmt_code == 3:
            np_fmt = 'u8'  # uint64
        elif fmt_code == 4:
            np_fmt = 'f4'  # float32
        elif fmt_code == 5:
            np_fmt = 'f8'  # float64
        elif fmt_code == 6:
            if wfm_version >= 3:
                np_fmt = 'u1'  # uint8
            else:
                raise WfmReadError(f"invalid data format or error in file {filename}")
        elif fmt_code == 7:
            if wfm_version >= 3:
                np_fmt = 'i1'  # int8
            else:
                raise WfmReadError(f"invalid data format or error in file {filename}")
        else:
            raise WfmReadError(f"invalid data format or error in file {filename}")

        # --- leer datos de la curva del frame seleccionado ---
        # offset tal como en MATLAB:
        offset = int(pos_before_updatespec + (info['N'] + 1) * 54 + (info['end_of_curve_buffer_offset'] - info['precharge_start_offset']) * (frame - 1) + info['data_start_offset'] + (startind - 1) * info['num_bytes_per_point'])
        f.seek(offset, os.SEEK_SET)

        # número total de puntos almacenados en archivo (en la porción de "data")
        nop_all = int((info['postcharge_start_offset'] - info['data_start_offset']) / info['num_bytes_per_point'])

        # nop: disponible desde startind hasta postcharge
        nop = nop_all - startind + 1

        # gestión de parametros datapoints, step, startind
        if datapoints is not None:
            # comprobar datapoints válido
            if datapoints < 1 or int(datapoints) != datapoints:
                # MATLAB: set to max number of datapoints and advertir
                datapoints = int(np.floor(nop / step))
                warnings.warn(f'"datapoints" input parameter must be a positive integer. Setting datapoints= {datapoints}.', UserWarning)
            nop_possible = int(np.floor(nop / step))
            if datapoints > nop_possible:
                warnings.warn(('The requested combination of input parameters datapoints, step and startind would require at least '
                               f'{datapoints*step + startind - 1} data points in {name_noext}. The actual number of data points in the trace is only {nop_all}. '
                               f'The number of data points returned is thus only {nop_possible} instead of {datapoints}.'), UserWarning)
                nop = nop_possible
            else:
                nop = int(datapoints)
        else:
            # si datapoints no especificado, tomar el máximo usando step
            nop = int(np.floor(nop / step))

        # ahora leer la porción de bytes que contiene nop_all puntos (desde startind), y luego sustituir/seleccionar
        # cuántos bytes necesitamos leer: (nop * step) * num_bytes_per_point   ??? No: necesitamos leer nop*step valores.
        # Mejor leer todos los nop_all valores completos disponibles y luego tomar el slice.
        # Para eso calculamos el número de bytes desde offset hasta postcharge_start_offset
        bytes_to_read = int((info['postcharge_start_offset'] - info['data_start_offset']) - (startind - 1) * info['num_bytes_per_point'])
        f.seek(offset, os.SEEK_SET)
        data_bytes = f.read(bytes_to_read)
        # interpretar el bloque con numpy según np_fmt y endianness
        np_dtype = np.dtype(endian + np_fmt)
        # si la longitud no es múltiplo del tamaño del dtype, recortamos
        itemsize = np_dtype.itemsize
        n_items = len(data_bytes) // itemsize
        if n_items <= 0:
            raise WfmReadError("No hay datos disponibles para leer (n_items<=0).")
        arr = np.frombuffer(data_bytes[:n_items * itemsize], dtype=np_dtype)

        # ahora seleccionar los valores: arr[0 : nop*step : step]
        # pero en MATLAB values = fread(fid, nop, format, info.num_bytes_per_point*(step-1), byteorder)
        # equivalencia: tomar el primer elemento, luego cada 'step'
        values = arr[0:(nop * step):step].astype(np.float64)  # convertir a float64 para seguridad

        # eje temporal t y escala y
        # t = info.id1.dim_offset + info.id1.dim_scale * (startind+(1:step:(nop*step))'-1);
        indices = startind + np.arange(0, nop * step, step)  # 1-based indices as in MATLAB
        # en MATLAB usan ' (columna). En Python dejamos como vector 1D
        t = id1['dim_offset'] + id1['dim_scale'] * (indices - 1)

        # y = info.ed1.dim_offset + info.ed1.dim_scale * values;
        y = ed1['dim_offset'] + ed1['dim_scale'] * values

        # over/under range: MATLAB usa
        # ind_over=find(values==info.ed1.over_range);
        # ind_under=find(values<=-info.ed1.over_range);
        ind_over = np.where(values == ed1['over_range'])[0]
        ind_under = np.where(values <= -ed1['over_range'])[0]

        # rellenar info final
        info['yunit'] = ed1['units']
        info['tunit'] = id1['units']
        info['yres'] = ed1['dim_resolution']
        # samplingrate = 1 / id1.dim_scale  (si dim_scale es spacing entre muestras)
        if id1['dim_scale'] != 0:
            info['samplingrate'] = 1.0 / id1['dim_scale']
        else:
            info['samplingrate'] = np.nan
        info['nop'] = int(nop)

        # En MATLAB imprimen advertencias si hay over/under; aquí no imprimimos por defecto,
        # pero preservamos el conteo en info
        info['n_over'] = int(len(ind_over))
        info['n_under'] = int(len(ind_under))

        # empaquetar los sub-structs en info para devolver
        info['ed1'] = ed1
        info['ed2'] = ed2
        info['id1'] = id1
        info['id2'] = id2

    # devolver arrays en forma numpy
    return y, t, info, ind_over, ind_under


# Si quieres ejecutar como script de prueba:
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Uso: python wfm2readframe.py <archivo.wfm> <frame> [datapoints] [step] [startind]")
    else:
        fname = sys.argv[1]
        frm = int(sys.argv[2])
        dp = int(sys.argv[3]) if len(sys.argv) > 3 else None
        st = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        si = int(sys.argv[5]) if len(sys.argv) > 5 else 1
        y, t, info, ind_over, ind_under = wfm2readframe(fname, frm, dp, st, si)
        print("Leídos", info['nop'], "puntos.")
        print("Over:", info['n_over'], "Under:", info['n_under'])

