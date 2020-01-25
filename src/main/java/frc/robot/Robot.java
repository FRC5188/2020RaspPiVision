/*----------------------------------------------------------------------------*/
/* Copyright (c) 2017-2018 FIRST. All Rights Reserved.                        */
/* Open Source Software - may be modified and shared by FRC teams. The code   */
/* must be accompanied by the FIRST BSD license file in the root directory of */
/* the project.                                                               */
/*----------------------------------------------------------------------------*/

package frc.robot;

import edu.wpi.first.wpilibj.Counter;
import edu.wpi.first.wpilibj.TimedRobot;
import edu.wpi.first.wpilibj.XboxController;
import edu.wpi.first.wpilibj.controller.PIDController;
import com.ctre.phoenix.motorcontrol.ControlMode;
import com.ctre.phoenix.motorcontrol.can.TalonSRX;
import com.ctre.phoenix.motorcontrol.can.VictorSPX;

import edu.wpi.first.networktables.NetworkTable;
import edu.wpi.first.networktables.NetworkTableEntry;
import edu.wpi.first.networktables.NetworkTableInstance;

public class Robot extends TimedRobot {
  
  private NetworkTableInstance inst;
  private NetworkTable table;
  private NetworkTableEntry xEntry;
  private NetworkTableEntry yEntry;
  private NetworkTableEntry pidP;
  private NetworkTableEntry pidI;
  private NetworkTableEntry pidD;
  private PIDController contr;

  private TalonSRX leftMotor1;
  private TalonSRX leftMotor2;
  
  private TalonSRX rightMotor1;
  private VictorSPX rightMotor2;
  
  private XboxController controller;
  private Counter m_LIDAR;
  //private PIDController lidarPID;
  @Override
  public void robotInit() {
    
    /*
    **** IMPORTANT ****
    This commit attempts to implement the lidar sensor, but it doesn't work.
    The turning code is still here, but commented out in order to test distance to target PID.
    ** Currently, this code does not work **
    Comments will be given on what was copied in from the lidar sensor.
    */
    // Begin Copy Paste Lidar Sample
    m_LIDAR = new Counter(0); //plug the lidar into PWM 0
    m_LIDAR.setMaxPeriod(1.00); //set the max period that can be measured
    m_LIDAR.setSemiPeriodMode(true); //Set the counter to period measurement
    m_LIDAR.reset();
    // End Copy Paste Lidar Sample
    
    this.inst = NetworkTableInstance.getDefault();
    this.table = inst.getTable("SmartDashboard");
    this.xEntry = table.getEntry("tape-x");
    this.yEntry = table.getEntry("tape-y");
    this.pidP = table.getEntry("pid/p");
    this.pidI = table.getEntry("pid/i");
    this.pidD = table.getEntry("pid/d");
    this.pidP.setDefaultDouble(0.00); // Good PID values found below
    this.pidI.setDefaultDouble(0.00); 
    this.pidD.setDefaultDouble(0.00);
    /* Decent PID values for turning (not the best at all)
    P: 0.005
    I: 0.003
    D: 0.07
    */
    contr = new PIDController(0.0, 0.0, 0.0); // Initialize with no values, import values from Shuffleboard
    contr.setSetpoint(0.0);
    leftMotor1 = new TalonSRX(0);
    leftMotor2 = new TalonSRX(1);
    rightMotor1 = new TalonSRX(2);
    rightMotor2 = new VictorSPX(3);
    leftMotor2.follow(leftMotor1);
    rightMotor2.follow(rightMotor1);
  }
  // Begin Copy Paste Lidar Sample
  final double off  = .2; //offset for sensor. test with tape measure
  
  @Override // NOTE: Robot Periodic, not Teleop (teleop is for PID distance testing)
  public void robotPeriodic() {
    double dist;
    System.out.println(m_LIDAR.get());
    if(m_LIDAR.get() < 1)
      dist = 0;
    else
      dist = (m_LIDAR.getPeriod()*1000000.0/10.0) - off; //convert to distance. sensor is high 10 us for every centimeter. 
    System.out.println(dist);
  }
  // End Copy Paste Lidar Sample

  public void teleopPeriodic() {
    // If tape not visible, 
    /*if(xEntry.getValue().getDouble() < 0) {
      leftMotor1.set(ControlMode.PercentOutput, 0.0);
      rightMotor1.set(ControlMode.PercentOutput, 0.0);
      return;
    }*/
    contr.setPID(this.pidP.getValue().getDouble(), this.pidI.getValue().getDouble(), this.pidD.getValue().getDouble());
    
    // * Turning Robot w/ Rasp Pi Camera Vision & PID
    /*
    double x = (xEntry.getValue().getDouble()-160.0);
    double motorPower = contr.calculate(x);
    leftMotor1.set(ControlMode.PercentOutput, motorPower);
    rightMotor1.set(ControlMode.PercentOutput, -motorPower);
    */

    // Attempting to implement lidar with PID
    System.out.println(m_LIDAR.get() + " " + m_LIDAR.getPeriod());
    if(m_LIDAR.get() < 1) {
      return;
    }
    double x = (m_LIDAR.getPeriod()*1000000.0/10.0)-off;
    double motorPower = contr.calculate(x)*0.3;
    leftMotor1.set(ControlMode.PercentOutput, motorPower);
    rightMotor1.set(ControlMode.PercentOutput, -motorPower);
    
    // * Testing to make sure motors work using Xbox Controller
    /*
    double motorPower = controller.getRawAxis(1);
    System.out.println(motorPower);
    leftMotor1.set(ControlMode.PercentOutput, motorPower);
    rightMotor1.set(ControlMode.PercentOutput, motorPower);
    */
    
  }
  
}
