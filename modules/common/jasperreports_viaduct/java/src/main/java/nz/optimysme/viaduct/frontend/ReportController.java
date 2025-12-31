package nz.optimysme.viaduct.frontend;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;

import nz.optimysme.viaduct.server.ReportRequest;
import nz.optimysme.viaduct.server.ViaductJasperReport;
import nz.optimysme.viaduct.server.ViaductResult;

/**
 * Request Controller for all reports.
 */
@Controller
@RequestMapping
public class ReportController
{
	@Autowired
	private ViaductJasperReport _engine;

	@RequestMapping (method = RequestMethod.POST)
	@ResponseBody
	public ViaductResult report (
		@RequestBody ReportRequest request)
	{
		return _engine.generate (request);
	}
}
