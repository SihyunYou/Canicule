using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Diagnostics;
using System.IO;

namespace ChatEtChien
{
    public partial class Form1 : Form
    {
        bool Fini = false;
        Thread t;

        public Form1()
        {
            if (File.Exists("log/etat.txt"))
            {
                File.Delete("log/etat.txt");
            }

            if (File.Exists("log/masse.txt"))
            {
                File.Delete("log/masse.txt");
            }

            t = new Thread(Lire);
            t.Start();
            
            InitializeComponent();
        }

        ~Form1()
        {
            Fini = true;
            t.Join();
        }

        int Premier = 0;
        int Dernier = 0;

        private void Lire()
        {
            while (!Fini)
            {
                try
                {
                    StreamReader sr = new StreamReader("log/etat.txt");
                    label3.Text = sr.ReadLine();
                    sr.Close();
                }
                catch(Exception)
                {

                }

                try
                {
                    StreamReader sr = new StreamReader("log/masse.txt");
                    string[] s = sr.ReadLine().Split(',');
                    sr.Close();

                    Premier = Convert.ToInt32(s[0]);
                    Dernier = Convert.ToInt32(s[1]);
                    int t = Premier - Dernier;

                    string p = t.ToString() + "\\ (";
                    if (t > 0)
                    {
                        p += "+";
                    }
                    else if(t < 0)
                    {
                        p += "-";
                    }
                    string q = Math.Round(Math.Abs(t) / (double)Dernier * 100, 3).ToString();
                    if("0" == q)
                    {
                        q = "0.000";
                    }
                    p += "%)";

                    label1.Text = String.Format("{0:#,0}", p);
                    label2.Text = String.Format("{0:#,0}", Dernier) + "\\"; }
                catch (Exception)
                {

                }

                Thread.Sleep(100);
            }
        }


        private void button1_Click(object sender, EventArgs e)
        {
            button1.SendToBack();
            Process.Start("cmd.exe", "/C trader.py");
        }

        private void button2_Click(object sender, EventArgs e)
        {
            button2.SendToBack();
        }
    }
}
