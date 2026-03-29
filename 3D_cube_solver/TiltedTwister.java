import java.awt.BorderLayout;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PipedInputStream;
import java.io.PipedOutputStream;
import java.io.PrintStream;

import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

import lejos.nxt.remote.NXTCommand;
import lejos.pc.comm.NXTComm;
import lejos.pc.comm.NXTCommException;
import lejos.pc.comm.NXTCommFactory;
import lejos.pc.comm.NXTInfo;

import org.kociemba.twophase.Search;

public class TiltedTwister {
	private static final byte INBOX = 11;
	private static final byte OUTBOX = 5;

	public static void main(String[] args) throws IOException {
	    JFrame frame = new JFrame();
	    final JTextArea area = new JTextArea();
	    area.setEditable(false);
	    frame.add(area);
	    frame.setSize(500, 500);
	    frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
	    frame.setVisible(true);

        // Add a scrolling text area
        area.setRows(20);
        frame.getContentPane().add(new JScrollPane(area), BorderLayout.CENTER);
	    PipedOutputStream os = new PipedOutputStream();
	    System.setOut(new PrintStream(os));
	    
	    final BufferedReader reader = new BufferedReader(
	          new InputStreamReader(new PipedInputStream(os)));
	    
	    new Thread(new Runnable() {
	       @Override
	       public void run() {
	          try {
	             for ( int c = -1; (c = reader.read()) != -1; ) {
	                area.append(Character.toString((char)c));
	                area.setCaretPosition( area.getText().length() );
	             }
	          } catch (IOException ioe) {
	          }
	       }
	    }).start();
	    
		System.out.println("Tilted Twister");
		System.out.println("Hans Andersson 2010");
		System.out.println("Two-Phase-Algorithm by Herbert Kociemba, http://kociemba.org/cube.htm");
		System.out.println("Initiating bluetooth...");
		NXTInfo[] nxtInfo = null;
		try {
			nxtInfo = NXTCommFactory.createNXTComm(NXTCommFactory.BLUETOOTH).search(null, NXTCommFactory.BLUETOOTH);
		} catch (NXTCommException e1) {
		}
		int connected=0;
		NXTComm[] nxtComm=new NXTComm[nxtInfo.length];
		NXTCommand[] nxtCommand = new NXTCommand[nxtInfo.length];
		for(int i=0;i<nxtInfo.length;i++)
		{
			try {
				nxtComm[i]=NXTCommFactory.createNXTComm(NXTCommFactory.BLUETOOTH);
				nxtCommand[i]=new NXTCommand();
				nxtComm[i].open(nxtInfo[i]);
				nxtCommand[i].setNXTComm(nxtComm[i]);
				connected++;
			} catch (NXTCommException e) {
			}
		}
		if(connected==0)
		{
			System.out.println("No brick connected. Aborting...");
			System.out.println("Good bye");
		}
		else
		{
			for(int i=0;i<nxtInfo.length;i++)
			{
				System.out.print(nxtInfo[i].name + " (" + nxtInfo[i].deviceAddress + ") ");
				if(nxtCommand[i].isOpen())
					System.out.println("connected");
				else
					System.out.println("not connected");
			}
			System.out.println("Initiating solver...");
			Search.solution("UUUUUURRRDRRDRRDRRFFFFFFFFFLLLDDDDDDLLULLULLUBBBBBBBBB", 30, 60, false);
			System.out.println("Ready");
			while(true){
				for(int i=0;i<nxtCommand.length;i++)
					if(nxtCommand[i].isOpen())
					{
						try {
							byte[] message = null;
							message = nxtCommand[i].messageRead(INBOX,(byte)0,true);
							if(message.length==55)
							{
								System.out.println("Request from " + nxtInfo[i].name + " (" + nxtInfo[i].deviceAddress + ") ");
								String msg = new String(message).substring(0,54);
								//Order of faces is different
								String cube=msg.substring(4*9,4*9+9)+msg.substring(2*9,2*9+9)+msg.substring(1*9,1*9+9)+msg.substring(5*9,5*9+9)+msg.substring(0*9,0*9+9)+msg.substring(3*9,3*9+9);
								System.out.println("Cube = " + cube);
								System.out.println("Searching solution...");
								String solution = Search.solution(cube, 30, 30, false);
								String response = "";
								if(solution.contains("Error"))
								{
									if(solution.charAt(solution.length() - 1)=='8')
										System.out.println("Timeout, no solution found within maximum time!");
									else
										System.out.println("Invalid cube, probably due to error in color scanning");
									response="ERROR";
								}
								else
								{
									System.out.println("Solution = " + solution);
									for(int pos=0;pos<solution.length();pos++)
									{
										switch(solution.charAt(pos))
										{
										case 'L':
										case 'F':
										case 'R':
										case 'B':
										case 'U':
										case 'D':
										{
											response+=solution.charAt(pos);
											break;
										}
										case '2':
										{
											response+=solution.charAt(pos-1);
											break;
										}
										case '\'':
										{
											response+=solution.charAt(pos-1);
											response+=solution.charAt(pos-1);
											break;
										}
										}
									}
								}
								response += '\u0000';
								nxtCommand[i].messageWrite(response.getBytes(), OUTBOX);
								System.out.println("Ready");
							}
						} catch (IOException e) {
						}
					}
			}
		}
	}
}
