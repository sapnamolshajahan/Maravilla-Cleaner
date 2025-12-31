# -*- coding: utf-8 -*-
import glob
import logging
from datetime import datetime
from os.path import basename, dirname, getmtime, relpath

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ViaductReport(models.Model):
    """
    Viaduct Resources: JRXML, images
    """
    _name = "viaduct.resource"
    _description = __doc__
    _sql_constraints = [
        ("unique_path", "unique(directory, name)", "Report Paths must be unique")
    ]

    ################################################################################
    # Fields
    ################################################################################
    name = fields.Char("Pathname", required=True)
    directory = fields.Char("Directory", required=True)
    jrxml = fields.Text("JRXML source", help="JRXML Source")
    mtime = fields.Datetime("Source Timestamp", required=True)
    content = fields.Binary("Resource Content", attachment=False)

    @api.model
    def inspect(self, pathname):
        """
        Build report records from inspecting the given source file's directory.

        :param pathname: source file absolute path
        :return: viaduct.report singleton for the report
        """
        src_dir = relpath(dirname(pathname))
        src_target = relpath(pathname)

        dir_files = self.search([("directory", "=", src_dir)])
        result, dir_files = self.inspect_jrxmls(src_dir, src_target, dir_files)
        dir_files = self.inspect_resources(src_dir, dir_files)

        # Remove unreferenced sources
        for resource in dir_files:
            _logger.debug(f"remove resource={resource.directory}/{resource.name}")
            resource.unlink()

        return result

    @api.model
    def inspect_jrxmls(self, src_dir, src_target, dir_files):
        """
        Look for jrxml source files.
        """
        target = None
        for jrxml in glob.glob(f"{src_dir}/*.jrxml"):
            src = basename(jrxml)
            mtime = datetime.fromtimestamp(getmtime(jrxml))

            rec = dir_files.filtered(lambda r: r.name == src)
            if rec:
                dir_files = dir_files - rec
                if rec.mtime < mtime:
                    rec.write(
                        {
                            "mtime": mtime,
                            "jrxml": self._read_file(jrxml),
                            "content": None,  # forces compilation on viaduct server
                        })
                    _logger.debug(f"updated source={jrxml}")
            else:
                rec = self.create(
                    [{
                        "name": src,
                        "directory": src_dir,
                        "mtime": mtime,
                        "jrxml": self._read_file(jrxml),
                    }])
                _logger.debug(f"created name={jrxml}")

            if jrxml == src_target:
                target = rec

        return target, dir_files

    @api.model
    def inspect_resources(self, src_dir, dir_files):
        """
        Look for other files of interest; ie image files.
        """
        patterns = ("*.png", "*.jpg", "*.svg")
        for pattern in patterns:
            for resource in glob.glob(f"{src_dir}/{pattern}"):
                src = basename(resource)
                mtime = datetime.fromtimestamp(getmtime(resource))

                rec = dir_files.filtered(lambda r: r.name == src)
                if rec:
                    dir_files = dir_files - rec
                    if rec.mtime < mtime:
                        rec.write(
                            {
                                "mtime": mtime,
                                "jrxml": None,
                                "content": self._read_file(resource, "rb"),
                            })
                        _logger.debug(f"updated resource={resource}")
                    continue

                self.create(
                    [{
                        "name": src,
                        "directory": src_dir,
                        "mtime": mtime,
                        "content": self._read_file(resource, "rb"),
                    }])
                _logger.debug(f"created resource={resource}")

        return dir_files

    def _read_file(self, source, mode="r"):
        """
        Read the source file
        """
        with open(source, mode) as src:
            return src.read()
