
n_files=length(dir('N175_0*.txt'));


M=[];
for i=1:n_files
    filenum=num2str(i-1);
    filebeg='N175_0';
    filename=[filebeg filenum];
    filename
    L = dlmread([filename '.txt']);
    M(:,i)=L;
%    M =[M load([filename '.txt'])];
end
dlmwrite('myFile.txt',M,'delimiter','\t','precision',3)
N=[];
for i=1:length(M);
    N(i,1)=i;
    N(i,2)=0;
end
for i=1:n_files
    N(:,2)=N(:,2)+M(:,i);
end
