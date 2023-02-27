import os.path


def output_file(crashLogger):
    # creating the output file with read & write permissions
    accessor = open("Application_Crash_Log.txt", "w+")
    print("CrashLogger file exists: " + str(os.path.exists("Application_Crash_Log.txt")))

    # Open file, write out each event from the testCase on its own line in the output file
    with open("Application_Crash_Log.txt", "w") as file:
        for crash in crashLogger:
            file.write("Crash Case:\n")
            for i in range(len(crash)):
                # writing to the text file
                file.write("%s\n" % crash[i])
            file.write("\n" * 2)
    accessor.close()
