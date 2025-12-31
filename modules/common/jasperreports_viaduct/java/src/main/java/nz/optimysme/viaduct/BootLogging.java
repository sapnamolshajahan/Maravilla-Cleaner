package nz.optimysme.viaduct;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.logging.log4j.core.config.ConfigurationSource;
import org.apache.logging.log4j.core.config.Configurator;

import jakarta.servlet.ServletContextEvent;
import jakarta.servlet.ServletContextListener;

/**
 * Kickstart log4j setup, as the out-of-the-box configuration doesn't appear to
 * be working properly.
 */
public class BootLogging
	implements ServletContextListener
{
	@Override
	public void contextInitialized (
		ServletContextEvent context)
	{
		String log4jProperties = context.getServletContext ().getInitParameter ("bootLogging");
		if (log4jProperties != null)
		{
			File config = new File (log4jProperties);
			if (config.canRead ())
			{
				try (InputStream is = new FileInputStream (config))
				{
					ConfigurationSource source = new ConfigurationSource (is, config);
					Configurator.initialize (null, source);

					Logger logger = LogManager.getLogger (BootLogging.class);
					logger.info ("viaduct log4j2 configuration=" + config);

				} catch (IOException e)
				{
					e.printStackTrace ();
				}
			}
		}
	}
}
