%CODE TO READ FILE 'DRONETEST2 (TUESDAY 23RD AUGUST 2016)' AND PRODUCE A 
%COLOURMAP SHOWING THE MEAN COUNT RATE [CPS] OF GAMMA RADIATION DETECTED 
%BY CAESIUM-137 SOURCE.
%AUTHOR: CHARLES D. ARROWSMITH

%(ENERGY OF PEAK CORRESPONDS TO THAT OF 662KEV AND TESTS SHOW THAT
%BACKGROUND RADIATION IS NEGLEGIBLE IN THIS CASE. NEVERTHELESS,
%OUR GRAPHIC IS TO SHOW ONLY THE CHANGE IN RADIATION DOSAGE SO BACKGROUND
%COUNTS CAN BE CONSIDERED IRRELEVANT IF ASSUMED ALMOST CONSTANT FOR SMALL 
%RANGE OF LOCATIONS.)

%We create an initial master array which we plan to fill with our data.
T = zeros(75,4);

%To obtain the data from all of our measurements, we must perform three
%loops.

%First loop over each direction:
for i=1:9;
   if i == 1;
        direction = 'N'; theta = pi/2;
   end
   if i == 2;
        direction = 'NE'; theta = pi/4;
   end
   if i == 3;
        direction = 'E'; theta = 0;
   end
   if i == 4;
        direction = 'SE'; theta = -pi/2;
   end
   if i == 5;
        direction = 'S'; theta = -pi/4;
   end
   if i == 6;
        direction = 'SW'; theta = -3*pi/4;
   end
   if i == 7;
        direction = 'W'; theta = pi;
   end
   if i == 8;
        direction = 'NW'; theta = 3*pi/4;
   end
   if i == 9;
        direction = 'C';
   end
      
   %For the file formats all except 'C', loop over height:
       for a=50:50:150; %Height does not need to get lower than 50cm. 
        %Drone is not flown lower than this to avoid collisions with ground.
        height=num2str(a);
        if i <= 8;
        %Now loop over all lengths.
          for b=50:50:150;
            length=num2str(b);
            
            %Finally loop over all detections.
            for c=1:9;
                filenum=num2str(c);
                L = dlmread(['C:\Users\Charlie Arrowsmith\Documents\MATLAB\dronetest2 (Tuesday 23rd August 2016)\'...
                    direction height '_' length '_' filenum '.txt']);
                M(:,c)=L; %Assign each set to a column of matrix M
            end
            %Now we calculate a matrix of mean counts per second in array P
            P=mean(M,2);
            %And we sum these for an interval which corresponds to the
            %Caesium-137 gamma radiation energy peak via decay of Barium-137
            S=sum(P(1332-100:1332+100));
            rowinT = (i-1)*9 + 0.06*a + 0.02*b - 3;  
            T(rowinT,1) = b*cos(theta);
            T(rowinT,2) = b*sin(theta);
            T(rowinT,3) = a;
            T(rowinT,4) = S;     
          end  
         end
       end

       %For the file format for 'C', loop over height only, since length=0:  
       if i == 9;
          for a=50:50:150;
            height=num2str(a);
            b = 0;
            for c=1:9;
              filenum=num2str(c);
              L = dlmread(['C:\Users\Charlie Arrowsmith\Documents\MATLAB\dronetest2 (Tuesday 23rd August 2016)\'...
                  direction height '_' filenum '.txt']);
              M(:,c)=L; %Assign each set to a column of matrix M
            end
            %Like before, we calculate a matrix of mean counts per second in array P
            P=mean(M,2);
            %And we sum these for an interval which corresponds to the
            %Caesium-137 gamma radiation energy peak via decay of Barium-137
            S=sum(P(1332-100:1332+100));
            
            %Assign the height, length and average no. of counts to our master
            %array:
            rowinT = (i-1)*9 + 0.02*a ;  
            T(rowinT,1) = b*cos(theta);
            T(rowinT,2) = b*sin(theta);
            T(rowinT,3) = a; 
            T(rowinT,4) = S;
          end
      end
end

%Define columns of master array as 'X', 'Y', 'Z' and 'V', where V is the
%mean CPS for each cartesian coordinate.
X = T(:,1);
Y = T(:,2);
Z = T(:,3);
V = T(:,4);

%Define a regular grid and interpolate the scattered data over the grid.
[Xq,Yq,Zq] = meshgrid(-150:5:150,-150:5:150,0:5:150);
Vq = griddata(X,Y,Z,V,Xq,Yq,Zq,'natural');
%This fits a hypersurface of the form v = f(x,y,z) to the scattered data. 
%The griddata function interpolates the surface at the query points 
%specified by (xq,yq,zq) and returns the interpolated values, vq. 
%The surface always passes through the data points defined by x, y and z.

figure; hold on;
%Create the slice planes and set the alpha data equal to the color data:
h=slice(Xq,Yq,Zq,Vq,[0],[0],[50,65,80,95,110]);
set(h,'EdgeColor','none',...
'FaceColor','interp',...
'FaceAlpha','interp');
alpha('color');
%Install the rampup alphamap and increase each value in the alphamap by .2
%to achieve the desired degree of transparency:
alphamap('rampup');
alphamap('increase',.2);
colormap jet;
colormapeditor;
%This alphamap displays the largest values of the function with the least 
%transparency and the amallest values display with the most transparency. 
%This enables us to see through the slice planes, while preserving the data.

%Finally, set limits of figure and label the axes:
xmin=-175;
xmax=175;
ymin=-175;
ymax=175;
zmin=0;
zmax=175;
limits=[xmin, xmax, ymin, ymax, zmin, zmax];
xlabel('Distance along ground east from source (cm)');
ylabel('Distance along ground north from source (cm)');
zlabel('Height of detector above ground (cm)');
title('Mean count rate [CPS] of gamma radiation detected by Caesium-137 source');
colorbar;
axis(limits);
%Remember to use the colormap editor to shift the bias of the colour in
%order to see clearly the more dramatic change in CPS closer to the source.