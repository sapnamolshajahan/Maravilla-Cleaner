Named Queue Job Channels
========================

Define Basic Channels for queue_job: **heavy** and **light**

Supporting Configuration must be included in rc files, eg::

    [queue_job]
    #
    # Base capacity of 10; with 2 sub-channels, "light", "heavy"
    # The base capacity _must_ be less than the number of workers
    #
    # "light" allows 8 active jobs, "heavy" allows 2 active job; for maximum total of 10 active jobs at any time
    channels = root:10, root.light:8, root.heavy:2

