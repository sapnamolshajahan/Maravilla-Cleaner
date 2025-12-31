package nz.optimysme.viaduct;

/**
 * Generic Exception class.
 */
public class ViaductException
	extends Exception
{
	public ViaductException (
		String message)
	{
		super (message);
	}

	public ViaductException (
		String message,
		Throwable t)
	{
		super (message, t);
	}
}
