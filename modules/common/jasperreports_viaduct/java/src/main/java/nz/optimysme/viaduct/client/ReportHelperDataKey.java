package nz.optimysme.viaduct.client;

public class ReportHelperDataKey
{
	public final int primary;
	public final Object secondaries[];

	public ReportHelperDataKey (
		int primary,
		Object secondaries[])
	{
		this.primary = primary;
		this.secondaries = secondaries;
	}

	public boolean equals (
		int id,
		Object args[])
	{
		if (id != primary || args.length != secondaries.length)
			return false;
		for (int i = 0; i < args.length; i++)
		{
			if (!secondaries[i].equals (args[i]))
				return false;
		}
		return true;
	}
}
