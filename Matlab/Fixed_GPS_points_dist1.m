% CODE TO MAP GPS FIXED POINT SIGNALS ONTO 3D COORDINATE SYSTEM TO
% INVESTIGATE THE DISTRIBUTION OF DETECTED POSITIONS. 
% AUTHOR: CHARLES D ARROWSMITH

clear all; % For the user if they are using multiple similar codes simultaneously.
num_readings = 3596; % This is the number of positions detected during the test.

% Create blank array of appropriate size:
M = zeros(num_readings,4);

% Now we loop over all the readings:
for i = 1:num_readings;
   
   % Import the data file as an array:
   filenum = num2str(i); 
   readData = textread(['/home/oceanw/Documents/Internship/Drone/Matlab/testing1'...
                     'dist_1_' filenum '.txt'],'%s');
   
   
   % The next stanzas of code divide the imported data into an array, M:           
   time_row = readData(1,1);              
   lat_row = readData(3,1);
   lon_row = readData(4,1);
   alt_row = readData(7,1);
   
   time_str_all = sprintf('%s\n', time_row{:});
   lat_str_all = sprintf('%s\n', lat_row{:});
   lon_str_all = sprintf('%s\n', lon_row{:});
   alt_str_all = sprintf('%s\n', alt_row{:});
   
   [time_label,] = strsplit(time_str_all,'=');
   [lat_label,] = strsplit(lat_str_all,'=');
   [lon_label,] = strsplit(lon_str_all,'=');
   [alt_label,] = strsplit(alt_str_all,'=');
   
   time_data = time_label(1,2);
   lat_value = lat_label(1,2);
   lon_value = lon_label(1,2);
   alt_value = alt_label(1,2);
   
   lat_str = sprintf('%s\n', lat_value{:});
   lon_str = sprintf('%s\n', lon_value{:});
   alt_str = sprintf('%s\n', alt_value{:});
   
   [lat_data,] = strsplit(lat_str,'+-'); 
   [lon_data,] = strsplit(lon_str,'+-');
   [alt_data,] = strsplit(alt_str,'+-'); 
   
   a = lat_data(1,1);
   lat = cellfun(@str2double,a);
   b = lon_data(1,1);
   lon = cellfun(@str2double,b);
   c = alt_data(1,1);
   alt = cellfun(@str2double,c);
   d = time_data(1,1);
   time = cellfun(@str2double,d);

   % The array M has 4 columns. The first three define the lla coordinates
   % and the fourth column is the corresponding time stamp.
   M(i,1) = lat*pi/180; % Remember to convert degrees to radians.
   M(i,2) = lon*pi/180;
   M(i,3) = alt;
   M(i,4) = time;
end

% Define the origin in lla coordinates as the first detected point and then
% transform this to ecef coordinates using the lla_to _ecef function.
lat_0 = M(1,1);
lon_0 = M(1,2);
alt_0 = M(1,3); 
[x_0,y_0,z_0] = lla_to_ecef(lat_0,lon_0,alt_0);

% Now convert lla coordinates to enu relative to the chosen origin as the
% first detected point. Arrange the data in array N:
N = zeros(num_readings,4);
for i=1:num_readings;
    lat = M(i,1);
    lon = M(i,2);
    alt = M(i,3);
    [x_dash,y_dash,z_dash] = lla_to_ecef(lat,lon,alt);
    [x,y,z] = ecef_to_enu(x_dash,y_dash,z_dash,lat_0,lon_0,x_0,y_0,z_0);

    N(i,1) = x;
    N(i,2) = y;
    N(i,3) = z;
    N(i,4) = M(i,4);
end

%Plot scatter diagram
x = N(:,1);
y = N(:,2);
z = N(:,3);
t = N(:,4);
pointsize = 20;
figure;
% In the scatter plot, let the point colour change with time to investigate
% any systematic shift of data points against time:
scatter3(x,y,z,pointsize,t);
xlabel('Distance east along from origin(m)');
ylabel('Distance north along from origin(m)');
zlabel('Distance along upward axis from origin(m)');
title('Distribution of detected GPS signals for a stationary point over time (1)');
h = colorbar;
ylabel(h,'Time(seconds)');
