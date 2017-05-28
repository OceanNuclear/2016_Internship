#include "SpectrometerDriver.h"
#include <stdio.h>
#include <stdlib.h>
#include <gps.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <ctype.h>

#define GPS_SUCCESS 1
#define GPS_ERROR -1
#define GPS_CONNECTION_ERROR -2
#define GPS_NO_FIX -3

#define WAIT_TIME_MICRO_SEC 1000
#define SEC_TO_NSEC 1000000000.0
#define SEC_TO_USEC 1000000.0
#define LOG_FILENAME "log.txt"
#define FAILURE -1
#define SUCCESS 0


// Find the NMEA standard checksum of a character array (string)
uint8_t nmea_crc(char data[])
{
	uint8_t checksum = 0;
	 for (size_t i = 0; data[i] != NULL; i++)
			 checksum = checksum ^ (uint8_t)data[i];

	 return checksum;
}


// Enable more frequent sampling
int setup_GPS_sampling_rate(char dev_name[], int interval_ms)
{
	float wait_time_s = 1.5;

    // Inform GPS of a pending switch to higher baud rate
	char tmp[150];
	sprintf(tmp, "echo -e \"\\$PMTK251,57600*2C\\r\\n\" > /dev/%s", dev_name);
	if (system(tmp) != 0)
	{
		write_to_log_and_stderr(LOG_FILENAME, "Unable to inform NMEA GPS of higher baud rate\n", "a");
		return FAILURE;
	}

    // Wait for GPS to hopefully have processed this
	usleep((int)(SEC_TO_USEC * wait_time_s));

    // Now use a higher baud rate when talking to the GPS
	sprintf(tmp, "stty -F /dev/%s 57600 clocal cread cs8 -cstopb -parenb", dev_name);
	if (system(tmp) != 0)
	{
		write_to_log_and_stderr(LOG_FILENAME, "Unable to set higher baud for USB device\n", "a");
		return FAILURE;
	}

    // Produce the command string for GPS to use higher sample rate
	char minor[50];
	sprintf(minor, "PMTK220,%u", interval_ms);

    // Determine command checksum (so GPS doesn't ignore it) & send GPS command
	char crc = nmea_crc(minor);
	sprintf(tmp, "echo -e \"\\$%s*%2X\\r\\n\" > /dev/%s", minor, crc, dev_name);

	if (system(tmp) != 0)
	{
		write_to_log_and_stderr(LOG_FILENAME, "Unable to set higher update rate for NMEA GPS device\n", "a");
		return FAILURE;
	}

	//system(tmp);
	write_to_log_and_stdout(LOG_FILENAME, "Successfully set higher baud rate!\n", "a");
	return SUCCESS;
}


// Reverse of setup_GPS_sampling_rate
int restore_GPS_sampling_rate(char dev_name[])
{
	char tmp[150];
	float wait_time_s = 1.5;

	sprintf(tmp, "echo -e \"\\$PMTK220,1000*1F\\r\\n\" > /dev/%s", dev_name);
	if (system(tmp) != 0)
	{
		write_to_log_and_stderr(LOG_FILENAME, "Unable to set lower update rate for NMEA GPS device\n", "a");
		return FAILURE;
	}

	sprintf(tmp, "echo -e \"\\$PMTK251,9600*17\\r\\n\" > /dev/%s", dev_name);
	if (system(tmp) != 0)
	{
		write_to_log_and_stderr(LOG_FILENAME, "Unable to inform NMEA GPS of lower baud rate\n", "a");
		return FAILURE;
	}

	usleep((int)(SEC_TO_USEC * wait_time_s));

	sprintf(tmp, "stty -F /dev/%s 9600 clocal cread cs8 -cstopb -parenb", dev_name);
	if (system(tmp) != 0)
	{
		write_to_log_and_stderr(LOG_FILENAME, "Unable to set lower baud for USB device\n", "a");
		return FAILURE;
	}

	//system(tmp);
	write_to_log_and_stdout(LOG_FILENAME, "Successfully set lower baud rate!\n", "a");
	return SUCCESS;
}


// Wait for GPS fix
int get_gps_fix(struct gps_data_t* gps_data)
{
	int status = GPS_NO_FIX;

    // gps_waiting returns 1 when data is available. Otherwise it waits until WAIT_TIME_MICRO_SEC elapses before returning 0
	while (gps_waiting(gps_data, WAIT_TIME_MICRO_SEC))
	{
		// Shouldn't happen, but handle just in case
		if(gps_read(gps_data)==-1)
			return GPS_ERROR;

		// Check fix is valid
		if (gps_data->status == STATUS_FIX && (gps_data->fix.mode == MODE_2D || gps_data->fix.mode == MODE_3D) &&
			!isnan(gps_data->fix.latitude) && !isnan(gps_data->fix.longitude))
			{
				status = GPS_SUCCESS;
			}
			else
				status = GPS_NO_FIX;
	}
    return status;
}


// Output to log file only
void write_to_log(char log_path[], char info[], char mode[])
{
	FILE* log_file = fopen(log_path, mode);
	fputs(info, log_file);
	fclose(log_file);
}


// Output to log file and console
void write_to_log_and_stdout(char log_path[], char info[], char mode[])
{
	write_to_log(log_path, info, mode);
	printf(info);
}


// Output to log file and error console
void write_to_log_and_stderr(char log_path[], char info[], char mode[])
{
	write_to_log(log_path, info, mode);
	fprintf(stderr, info);
}


// Parse program command line arguments
int parse_args(int argc, char* argv[], char **t_str, char **f_str, int *just_gps, float *prog_duration, int *use_high_sample_rate)
{
	int c;
	opterr = 0;
	char log_buffer[100];

	while ((c=getopt(argc, argv, "t:f:pd:l")) != -1)
	{
		switch(c)
		{
			case 't':
				*t_str = optarg;
				break;
			case 'd':
				*prog_duration = atof(optarg);
				break;
			case 'f':
				*f_str = optarg;
				break;
			case 'p':
				*just_gps = 1;
				break;
			case 'l':
				*use_high_sample_rate = 0;
				break;

			case '?':
				if (optopt == 't' || optopt == 'f' || optarg == 'd')
				{
					sprintf(log_buffer, "Option -%c requires an argument.\n", optopt);
					write_to_log_and_stderr(LOG_FILENAME, log_buffer, "a");
				}
				else if (isprint(optopt))
				{
					sprintf(log_buffer, "Unknown option -%c.\n", optopt);
					write_to_log_and_stderr(LOG_FILENAME, log_buffer, "a");
				}
				else
				{
					write_to_log_and_stderr(LOG_FILENAME, "Unknown option character.\n", "a");
				}
				return FAILURE;

			default:
				return FAILURE;
		}
	}
	return SUCCESS;
}


// Custom sleep function, call usleep but invoke no context switch if t == 0
int sleepu(int t)
{
	if (t)
		return usleep(t);
	return 0;
}


int main(int argc, char* argv[])
{
	time_t raw_time;
	struct tm *time_info_ptr;

	time(&raw_time);
	time_info_ptr = localtime(&raw_time);

	char log_buffer[150];

	sprintf(log_buffer, "Started! at %s\n", asctime(time_info_ptr));
	write_to_log_and_stdout(LOG_FILENAME, log_buffer, "w");

	// Parse command line args
	char *t_str = NULL;
	char *f_str = NULL;
	int just_gps = 0;
	int use_high_sample_rate = 1;
	float max_runtime = -1.0;

	// Ensure args are valid
	if (parse_args(argc, argv, &t_str, &f_str, &just_gps, &max_runtime, &use_high_sample_rate) == FAILURE)
		return 1;

    // Validate file pattern string and time interval string (not NULL)
	if (f_str == NULL || t_str == NULL)
	{
		write_to_log_and_stderr(LOG_FILENAME, "Both file name pattern and time interval are required args.\n", "a");
		return 1;
	}

    // Validate high sample rate flag
	if (use_high_sample_rate < 0 || use_high_sample_rate > 1)
	{
		write_to_log_and_stderr(LOG_FILENAME, "Use high sampling rate arg (r) must be either 0 or 1.\n", "a");
		return 1;
	}

	// Parse time interval
	double interval_time = strtof(t_str, NULL);

	sprintf(log_buffer, "Time interval %fs\n", interval_time);
	write_to_log_and_stdout(LOG_FILENAME, log_buffer, "a");

	// Parse format for records
	const char* format_path = f_str;
	if (strstr(format_path, "%d") == NULL)
	{
		sprintf(log_buffer, "Invalid record filename pattern %s\n", format_path);
		write_to_log_and_stdout(LOG_FILENAME, log_buffer, "a");
		return 1;
	}

	sprintf(log_buffer, "Record filename pattern %s\n", format_path);
	write_to_log_and_stdout(LOG_FILENAME, log_buffer, "a");

	// Setup higher data rate (5 HZ)
	if (use_high_sample_rate)
	{
		if (setup_GPS_sampling_rate("ttyUSB0", 200) == FAILURE)
			return 1;

		write_to_log_and_stdout(LOG_FILENAME, "Using high data rate\n", "a");
	}

	// Kromek radiation detector ID
	unsigned int detector_id = 0;

	// Can we just take GPS readings, and ignore KROMEK?
	if (just_gps)
		write_to_log_and_stdout(LOG_FILENAME, "Just using GPS\n", "a");

	else
	{
		// Initialise the library with no error callback (not recommended)
		kr_Initialise(NULL, NULL);

		detector_id = kr_GetNextDetector(0);
		if (detector_id == 0)
		{
			sprintf(log_buffer, "No spectrometer devices found!\n");
			write_to_log_and_stdout(LOG_FILENAME, log_buffer, "a");
			return 1;
		}

		// Get detector info
		char nameBuffer[200];
		int nameLength = 200;
		kr_GetDeviceName(detector_id, nameBuffer, nameLength, &nameLength);
	}

	////////////// File data
	char filename[100];
	unsigned int file_number = 0;

	sprintf(log_buffer, "Waiting for GPS!\n");
	write_to_log_and_stdout(LOG_FILENAME, log_buffer, "a");

	////////////// GPS
	struct gps_data_t gps_data;

    // Connect
    if(gps_open("localhost", "2947", &gps_data)<0)
    {
        sprintf(log_buffer, "Error connecting to GPS!\n");
        write_to_log_and_stdout(LOG_FILENAME, log_buffer, "a");
        return 1;
    }

    // Register for updates
    gps_stream(&gps_data, WATCH_ENABLE | WATCH_JSON, NULL);

	// Purge all the records that we accumulated whilst we waited for the higher data rate to be setup.
	// This takes finite time and would have made the number of records indeterminate
	while (get_gps_fix(&gps_data) != GPS_SUCCESS)
		;

    ////////////// Timing
    // Not to be compared to sleep data
    struct timespec start, current;
    clock_gettime(CLOCK_MONOTONIC, &start);
    int sleep_duration = (int)interval_time * SEC_TO_USEC;

	int is_running = 1;

	while (is_running)
	{
		while (get_gps_fix(&gps_data) != GPS_SUCCESS)
			;

		unsigned int spectrum[TOTAL_RESULT_CHANNELS] = {0};
		unsigned int real_time_ms = 0;
		unsigned int live_time_ms = 0;
		unsigned int total_counts = 0;

		// Sleep for data
		if (!just_gps)
		{
			kr_BeginDataAcquisition(detector_id, 0, 0);
			sleepu(sleep_duration);
			kr_StopDataAcquisition(detector_id);

			kr_GetAcquiredData(detector_id, spectrum, &total_counts, &real_time_ms, &live_time_ms);
			kr_ClearAcquiredData(detector_id);

			printf("Acquiring Data...\n");
		}
		else
			sleepu(sleep_duration);


		// Open file
		sprintf(filename, format_path, file_number);
		FILE* output_file = fopen(filename, "w");

		if (output_file == NULL)
		{
			sprintf(log_buffer, "Error opening file!\n");
			write_to_log_and_stderr(LOG_FILENAME, log_buffer, "a");
	        return 1;
		}

		// Get current timestamp
		clock_gettime(CLOCK_MONOTONIC, &current);
		double elapsed_seconds = (current.tv_sec - start.tv_sec) + (current.tv_nsec - start.tv_nsec) / SEC_TO_NSEC;

		// Write meta data
		fprintf(output_file, "#prog_timestamp=%f\n", elapsed_seconds);
		fprintf(output_file, "#gps_timestamp=%f+-%f\n", gps_data.fix.time, gps_data.fix.ept);

		// Write GPS
		fprintf(output_file, "#latitude=%f+-%f\n", gps_data.fix.latitude, gps_data.fix.epy);
		fprintf(output_file, "#longitude=%f+-%f\n", gps_data.fix.longitude, gps_data.fix.epx);

		fprintf(output_file, "#speed=%f+-%f\n", gps_data.fix.speed, gps_data.fix.eps);
		fprintf(output_file, "#climb=%f+-%f\n", gps_data.fix.climb, gps_data.fix.epc);

		if (gps_data.fix.mode == MODE_3D)
			fprintf(output_file, "#altitude=%f+-%f\n", gps_data.fix.altitude, gps_data.fix.epv);

		// Don't write irrelevant data
		if (!just_gps)
		{
			fprintf(output_file, "#real_time=%d\n", real_time_ms);
			fprintf(output_file, "#live_time=%d\n", live_time_ms);
			fprintf(output_file, "#sleep_time=%d\n", sleep_duration/1000);
		}

		// Write data concerning spectrum
		for (int i=0; i < TOTAL_RESULT_CHANNELS; i++)
			fprintf(output_file, "%d\n", spectrum[i]);

		fclose(output_file);
		printf("Logged entry %d!\n", file_number);

		file_number++;

		// End program after f seconds elapsed
		if (max_runtime > 0 && elapsed_seconds >= max_runtime)
			break;
	}

    // Cleanup GPS
    gps_stream(&gps_data, WATCH_DISABLE, NULL);
    gps_close(&gps_data);

    //if (result_code == GPS_ERROR)
    //{
    //	gps_stream(gps_data, WATCH_DISABLE, NULL);
    //	gps_close(gps_data);
    //}

	// Cleanup the library
	if (!just_gps)
		kr_Destruct();

	// Setup higher data rate (5 HZ)
	if (use_high_sample_rate)
	{
			if (restore_GPS_sampling_rate("ttyUSB0") == FAILURE)
				return 1;
	}

	write_to_log_and_stdout(LOG_FILENAME, "Finished recording entry!\n", "a");

	return 0;
}
