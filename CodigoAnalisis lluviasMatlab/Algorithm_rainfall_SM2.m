% Supplementary material
% Modificacion referenciada en:
% al usar referenciar:
% C. Isaza, D. Duque, S. Buritica and P. Caicedo. “Automatic identification of Landscape Transformation using acoustic recordings classification”, Ecological Informatics, ISSN: 15749541. SUBMITTED 2019.
%
% Original paper: Automatic Identification of Rainfall in Acoustic Recordings
% by Carol Bedoya, Claudia Isaza, Juan M. Daza, and José D. López
% This code performs the analysis of rainfall in several recordings within several folders 
% 
% Inputs:
% 1. rutain   -- Root path in which the recordings are located.
% 2. rutaout  -- Folder in which the output files will be saved.
% 3. namefile -- Output files name 
%
%The output files are a figure showing the mean PSD in the rain band and the signal to noise ratio;
%and a matlab file containing all mean PSD values, SNR values and the list of good recordings.


clc; clear all; close all % this command cleans the workspace and closes other windows.

%% Inputs -- please set the next parameters in accordance with your data %%

rutain  = 'G:\Bioacustica\Caribe\2016\5072\20160407\'; %copy here the root path with the recordings.
rutaout = 'C:\Users\dcdm1\Google Drive\'; %copy here the output path.
namefile = 'PSD_5072_20160407'; %filename for output files.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Tsnr	= 3.3;		% SNR threshold
h = dir(fullfile(rutain, '*.wav')); %recordings
nrecords = length(h);

meanPSD = zeros(nrecords, 1);
%snrPSD = zeros(nrecords, 1);
%% Algorithm

for i = 1:nrecords % each value of i corresponds to one specific recording
 
	try
		[x,FS] = audioread([rutain h(i).name]); % this line is for reading each recording
	catch
		continue %Some recordings are corrupted and can't be read, we will omit such recordings with this.
    end
    
	p	= pwelch(x(:,1),512); % power spectral density (monochannel), if your recording is stereo: 1 - left , 2 - right. Step 1 in Algorithm 2.1

	limite_inf = round(length(p)*(600*2/FS));	% minimum frequency of the rainfall frequency band (approx. 600 Hz)
	limite_sup = round(length(p)*(1200*2/FS));	% maximum frequency of the rainfall frequency band (approx. 1200 Hz)
	a	= p(limite_inf:limite_sup);			% section of interest of the power spectral density. Step 2 in Algorithm 2.1

	mean_a	= mean(a); % mean of the PSD in the frequency band of interest. Upper part of the step 3 in Algorithm 2.1
	std_a	= std(a);  % standard deviation of the PSD in the frequency band of interest. Lower part of the step 3 in in Algorithm 2.1

	c		= mean_a/std_a;		% signal to noise ratio of the analyzed recording. Step 3 in Algorithm 2.1

	meanPSD(i) = mean_a;
	%snrPSD(i) = c;

	display([num2str(i),' of ', num2str(length(h))]) % display the number of recordings processed

	month(i)=str2num(h(i).name(end-14:end-13));
	day(i)=str2num(h(i).name(end-12:end-11));
	hour(i)=str2num(h(i).name(end-9:end-8));
	minu(i)=str2num(h(i).name(end-7:end-6));

	date(i,:)=[month(i) day(i) hour(i) minu(i)];
end

meanPSD_nozeros = meanPSD(meanPSD ~= 0);
Tmean = (mean(meanPSD_nozeros)+geomean(meanPSD_nozeros))/2;
    
files_cell = struct2cell(h); %Cell with recordings absolute paths 
names_cell = files_cell(1, :); %Cell with recordings filenames    
good_files = names_cell(meanPSD <= Tmean & meanPSD ~= 0)'; % 
 

 %% Plots of the Mean Values of the Power Spectral Density and the Signals to Noise Ratios
%subplot(2,1,1)
stem(meanPSD,'LineWidth',3)
hold on
plot(Tmean*ones(1,length(meanPSD)),'r','LineWidth',3)
set(gca,'FontSize',16);
set(gcf,'Color',[1 1 1])
set(gca,'XTick',[]);
title('Mean Values of the Power Spectral Density', 'FontSize',30, 'FontName','Times New Roman')
ylabel('(Watts/Hz)/Min', 'FontSize',24, 'FontName','Times New Roman')
legend('mean(a)','Tmean')

%subplot(2,1,2)
%stem(snrPSD,'LineWidth',3)
%hold on
%plot(Tsnr*ones(1,length(snrPSD)),'r','LineWidth',3)
%set(gca,'FontSize',16);
%set(gcf,'Color',[1 1 1])
%title('Signal to Noise Ratios', 'FontSize',30, 'FontName','Times New Roman')
%xlabel('Recording', 'FontSize',24, 'FontName','Times New Roman')
%legend('c','Tsnr')

%% Save Data 
set(gcf,'units','normalized','outerposition',[0 0 1 1])
saveas(gcf, namefile, 'fig');
save([rutaout, namefile], 'meanPSD', 'good_files');


%% model
% this line maps the elements of the rainfall vector that contain rainfall activity (i.e. elements greater than 0) from Watt/hz to mm of rain.
% This parameters were settled in accordance with our recorder. Comment this part of code if you have not fitted your model.

%rainfall(logical(rainfall>0)) = 200.2*rainfall(logical(rainfall>0)) + 0.004318; flag=1;

%% Feature Scaling
%%% Uncomment these lines ONLY if the previous step is commented.
%%% Theselines map from normalized power to mm of rain.
%rainfall_norm=(rainfall-min(rainfall))/(max(rainfall)-min(rainfall)); flag=1;
%rainfall(logical(rainfall>0))=1.563*rainfall_norm(logical(rainfall>0))+0.0211;


%% Plot of the rainfall in the recordings 

% figure
% stem(rainfall, 'LineWidth',3)
% set(gca,'FontSize',16);
% set(gcf,'Color',[1 1 1])
% title('Rainfall Intensity', 'FontSize',30, 'FontName','Times New Roman')
% xlabel('Recording', 'FontSize',24, 'FontName','Times New Roman')
% if flag==1;
% ylabel('Millimeters of Rain/Min', 'FontSize',24, 'FontName','Times New Roman')
% else
% ylabel('(Watts/Hz)/Min', 'FontSize',24, 'FontName','Times New Roman')
% end

%% Rainfall per month
%figure
% for j=1:12 
%     f=find(month==j); 
%     rain_month(j,:)=[j, sum(rainfall(f))]; 
% end
% bar(rain_month(:,1),rain_month(:,2), 'LineWidth',3,'BarWidth',0.6)
% set(gca,'FontSize',16);
% set(gcf,'Color',[1 1 1])
% title('Monthly Rainfall', 'FontSize',30, 'FontName','Times New Roman')
% xlabel('Month', 'FontSize',24, 'FontName','Times New Roman')
% set(gca,'XTickLabel',{'January','February','March','April','May','June','July','August','September','October','November','December'},'FontSize',16);
% if flag==1;
% ylabel('Millimeters of Rain', 'FontSize',24, 'FontName','Times New Roman')
% else
% ylabel('Watts/Hz', 'FontSize',24, 'FontName','Times New Roman')
% end

%% Rainfall per day
%figure
% for k=1:31 
%     ff=find(day==k); 
%     rain_day(k,:)=[k, sum(rainfall(ff))];
% end 
% bar(rain_day(:,1),rain_day(:,2), 'r', 'LineWidth',3,'BarWidth',0.6)
% set(gca,'FontSize',16);
% set(gcf,'Color',[1 1 1])
% title('Daily Rainfall', 'FontSize',30, 'FontName','Times New Roman')
% xlabel('Day', 'FontSize',24, 'FontName','Times New Roman')
% if flag==1;
% ylabel('Millimeters of Rain', 'FontSize',24, 'FontName','Times New Roman')
% else
% ylabel('Watts/Hz', 'FontSize',24, 'FontName','Times New Roman')
% end