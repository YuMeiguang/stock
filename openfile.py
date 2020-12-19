try:
  fh = open("testfile","w")
  fh.write("this is a file")
except IOError:
  print("this is a error ")

else:
  print("write file success")
  fh.close()
